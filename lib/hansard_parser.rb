require 'speech'
require 'mechanize_proxy'
require 'configuration'
require 'debates'
require 'builder'

# Monkey Patch XML Builder to sort the attributes, so that they are in alphabetical order.
# This makes it easier to do simple diffs between XML files
module Builder
  class XmlMarkup < XmlBase
    # Insert the attributes (given in the hash).
    def _insert_attributes(attrs, order=[])
      return if attrs.nil?
      order.each do |k|
        v = attrs[k]
        @target << %{ #{k}="#{_attr_value(v)}"} if v # " WART
      end
      sorted_attrs = attrs.sort {|a,b| a.first.to_s <=> b.first.to_s}
      sorted_attrs.each do |k, v|
        @target << %{ #{k}="#{_attr_value(v)}"} unless order.member?(k) # " WART
      end
    end
  end
end

class UnknownSpeaker
  def initialize(name)
    @name = name
  end
  
  def id
    "unknown"
  end
  
  def name
    Name.title_first_last(@name)
  end
end

require 'rubygems'
require 'log4r'

class HansardParser
  attr_reader :logger
  
  def initialize(people)
    @people = people
    conf = Configuration.new
    
    # Set up logging
    @logger = Log4r::Logger.new 'HansardParser'
    # Log to both standard out and the file set in configuration.yml
    @logger.add(Log4r::Outputter.stdout)
    @logger.add(Log4r::FileOutputter.new('foo', :filename => conf.log_path, :trunc => false,
      :formatter => Log4r::PatternFormatter.new(:pattern => "[%l] %d :: %M")))
  end
  
  def parse_date(date, xml_filename)
    debates = Debates.new(date)
    
    @logger.info "Parsing speeches for #{date.strftime('%a %d %b %Y')}..."
    
    # Required to workaround long viewstates generated by .NET (whatever that means)
    # See http://code.whytheluckystiff.net/hpricot/ticket/13
    Hpricot.buffer_size = 400000

    agent = MechanizeProxy.new
    agent.cache_subdirectory = date.to_s

    url = "http://parlinfoweb.aph.gov.au/piweb/browse.aspx?path=Chamber%20%3E%20House%20Hansard%20%3E%20#{date.year}%20%3E%20#{date.day}%20#{Date::MONTHNAMES[date.month]}%20#{date.year}"
    begin
      page = agent.get(url)
      # HACK: Don't know why if the page isn't found a return code isn't returned. So, hacking around this.
      if page.title == "ParlInfo Web - Error"
        throw "ParlInfo Web - Error"
      end
    rescue
      logger.warn "Could not retrieve overview page for date #{date}"
      return
    end
    # Structure of the page is such that we are only interested in some of the links
    page.links[30..-4].each do |link|
      parse_sub_day_page(link.to_s, agent.click(link), debates, date)
      # This ensures that every sub day page has a different major count which limits the impact
      # of when we start supporting things like written questions, procedurial text, etc..
      debates.increment_major_count
    end
    
    debates.output(xml_filename)
  end
  
  def parse_sub_day_page(link_text, sub_page, debates, date)
    # Only going to consider speeches for the time being
    if link_text =~ /^Speech:/ || link_text =~ /^QUESTIONS WITHOUT NOTICE:/
      # Link text for speech has format:
      # HEADING > NAME > HOUR:MINS:SECS
      split = link_text.split('>').map{|a| a.strip}
      logger.error "Expected split to have length 3" unless split.size == 3
      time = split[2]
      parse_sub_day_speech_page(sub_page, time, debates, date)
    elsif link_text == "Official Hansard" || link_text =~ /^Start of Business/ || link_text == "Adjournment"
      # Do nothing - skip this entirely
    elsif link_text =~ /^Procedural text:/ || link_text =~ /^QUESTIONS IN WRITING:/ || link_text =~ /^Division:/
      logger.warn "Not yet supporting: #{link_text}"
    else
      logger.warn "Unsupported: #{link_text}"
    end
  end

  def parse_sub_day_speech_page(sub_page, time, debates, date)
    top_content_tag = sub_page.search('div#contentstart').first
    throw "Page on date #{date} at time #{time} has no content" if top_content_tag.nil?
    
    # Extract permanent URL of this subpage. Also, quoting because there is a bug
    # in XML Builder that for some reason is not quoting attributes properly
    url = quote(sub_page.links.text("[Permalink]").uri.to_s)

    newtitle = sub_page.search('div#contentstart div.hansardtitle').map { |m| m.inner_html }.join('; ')
    newsubtitle = sub_page.search('div#contentstart div.hansardsubtitle').map { |m| m.inner_html }.join('; ')
    # Replace any unicode characters
    newtitle = replace_unicode(newtitle)
    newsubtitle = replace_unicode(newsubtitle)

    debates.add_heading(newtitle, newsubtitle, url)

    speaker = nil
    top_content_tag.children.each do |e|
      class_value = e.attributes["class"]
      if e.name == "div"
        if class_value == "hansardtitlegroup" || class_value == "hansardsubtitlegroup"
        elsif class_value == "speech0" || class_value == "speech1"
          parse_speech_blocks(e.children[1..-1], speaker, time, url, debates, date)
        elsif class_value == "motionnospeech" || class_value == "subspeech0" || class_value == "subspeech1"
          parse_speech_block(e, speaker, time, url, debates, date)
        else
          throw "Unexpected class value #{class_value} for tag #{e.name}"
        end
      elsif e.name == "p"
        parse_speech_block(e, speaker, time, url, debates, date)
      elsif e.name == "table"
        if class_value == "division"
          # Ignore (for the time being)
        else
          throw "Unexpected class value #{class_value} for tag #{e.name}"
        end
      else
        throw "Unexpected tag #{e.name}"
      end
    end
  end
  
  def parse_speech_block(e, speaker, time, url, debates, date)
    speakername = extract_speakername(e)
    # Only change speaker if a speaker name was found
    speaker = lookup_speaker(speakername, date) if speakername
    debates.add_speech(speaker, time, url, clean_speech_content(url, e))
  end
  
  def parse_speech_blocks(content, speaker, time, url, debates, date)
    content.each do |e|
      parse_speech_block(e, speaker, time, url, debates, date)
    end
  end
  
  def extract_speakername(content)
    # Try to extract speaker name from talkername tag
    tag = content.search('span.talkername a').first
    tag2 = content.search('span.speechname').first
    if tag
      name = tag.inner_html
      # Now check if there is something like <span class="talkername"><a>Some Text</a></span> <b>(Some Text)</b>
      tag = content.search('span.talkername ~ b').first
      # Only use it if it is surrounded by brackets
      if tag && tag.inner_html.match(/\((.*)\)/)
        name += " " + $~[0]
      end
    elsif tag2
      name = tag2.inner_html
    # If that fails try an interjection
    elsif content.search("div.speechType").inner_html == "Interjection"
      text = strip_tags(content.search("div.speechType + *").first)
      m = text.match(/([a-z].*) interjecting/i)
      if m
        name = m[1]
      else
        m = text.match(/([a-z].*)—/i)
        if m
          name = m[1]
        else
          name = nil
        end
      end
    end
    name
  end
  
  # Replace unicode characters by their equivalent
  def replace_unicode(text)
    t = text.gsub("\342\200\230", "'")
    t.gsub!("\342\200\231", "'")
    t.gsub!("\342\200\224", "-")
    t.each_byte do |c|
      if c > 127
        logger.warn "Found invalid characters in: #{t.dump}"
      end
    end
    t
  end
  
  def clean_speech_content(base_url, content)
    doc = Hpricot(content.to_s)
    doc.search('div.speechType').remove
    doc.search('span.talkername ~ b').remove
    doc.search('span.talkername').remove
    doc.search('span.talkerelectorate').remove
    doc.search('span.talkerrole').remove
    doc.search('hr').remove
    make_motions_and_quotes_italic(doc)
    remove_subspeech_tags(doc)
    fix_links(base_url, doc)
    make_amendments_italic(doc)
    fix_attributes_of_p_tags(doc)
    fix_attributes_of_td_tags(doc)
    fix_motionnospeech_tags(doc)
    # Do pure string manipulations from here
    text = doc.to_s
    text = text.gsub("(\342\200\224)", '')
    text = text.gsub(/([^\w])\342\200\224/) {|m| m[0..0]}
    text = text.gsub(/\(\d{1,2}.\d\d a.m.\)/, '')
    text = text.gsub(/\(\d{1,2}.\d\d p.m.\)/, '')
    text = text.gsub('()', '')
    # Look for tags in the text and display warnings if any of them aren't being handled yet
    text.scan(/<[a-z][^>]*>/i) do |t|
      m = t.match(/<([a-z]*) [^>]*>/i)
      if m
        tag = m[1]
      else
        tag = t[1..-2]
      end
      allowed_tags = ["b", "i", "dl", "dt", "dd", "ul", "li", "a", "table", "td", "tr"]
      if !allowed_tags.include?(tag) && t != "<p>" && t != '<p class="italic">'
        throw "Tag #{t} is present in speech contents: " + text
      end
    end
    doc = Hpricot(text)
    #p doc.to_s
    doc
  end
  
  def fix_motionnospeech_tags(content)
    replace_with_inner_html(content, 'div.motionnospeech')
    content.search('span.speechname').remove
    content.search('span.speechelectorate').remove
    content.search('span.speechrole').remove
    content.search('span.speechtime').remove
  end
  
  def fix_attributes_of_p_tags(content)
    content.search('p.parabold').wrap('<b></b>')
    content.search('p').each do |e|
      class_value = e.get_attribute('class')
      if class_value == "block" || class_value == "parablock" || class_value == "parasmalltablejustified" ||
          class_value == "parasmalltableleft" || class_value == "parabold"
        e.remove_attribute('class')
      elsif class_value == "paraitalic"
        e.set_attribute('class', 'italic')
      elsif class_value == "italic" && e.get_attribute('style')
        e.remove_attribute('style')
      end
    end
  end
  
  def fix_attributes_of_td_tags(content)
    content.search('td').each do |e|
      e.remove_attribute('style')
    end
  end
  
  def fix_links(base_url, content)
    content.search('a').each do |e|
      href_value = e.get_attribute('href')
      if href_value.nil?
        # Remove a tags
        e.swap(e.inner_html)
      else
        e.set_attribute('href', URI.join(base_url, href_value))
      end
    end
    content
  end
  
  def replace_with_inner_html(content, search)
    content.search(search).each do |e|
      e.swap(e.inner_html)
    end
  end
  
  def make_motions_and_quotes_italic(content)
    content.search('div.motion p').set(:class => 'italic')
    replace_with_inner_html(content, 'div.motion')
    content.search('div.quote p').set(:class => 'italic')
    replace_with_inner_html(content, 'div.quote')
    content
  end
  
  def make_amendments_italic(content)
    content.search('div.amendments div.amendment0 p').set(:class => 'italic')
    content.search('div.amendments div.amendment1 p').set(:class => 'italic')
    replace_with_inner_html(content, 'div.amendment0')
    replace_with_inner_html(content, 'div.amendment1')
    replace_with_inner_html(content, 'div.amendments')
    content
  end
  
  def remove_subspeech_tags(content)
    replace_with_inner_html(content, 'div.subspeech0')
    replace_with_inner_html(content, 'div.subspeech1')
    content
  end
  
  def quote(text)
    text.sub('&', '&amp;')
  end

  def lookup_speaker(speakername, date)
    throw "speakername can not be nil in lookup_speaker" if speakername.nil?

    # HACK alert (Oh you know what this whole thing is a big hack alert)
    if speakername =~ /^the speaker/i
      member = @people.house_speaker(date)
    # The name might be "The Deputy Speaker (Mr Smith)". So, take account of this
    elsif speakername =~ /^the deputy speaker/i
      # Check name in brackets
      match = speakername.match(/^the deputy speaker \((.*)\)/i)
      if match
        #logger.warn "Deputy speaker is #{match[1]}"
        speakername = match[1]
        name = Name.title_first_last(speakername)
        member = @people.find_member_by_name_current_on_date(name, date)
      else
        member = @people.deputy_house_speaker(date)
      end
    else
      # Lookup id of member based on speakername
      name = Name.title_first_last(speakername)
      member = @people.find_member_by_name_current_on_date(name, date)
    end
    
    if member.nil?
      logger.warn "Unknown speaker #{speakername}"
      member = UnknownSpeaker.new(speakername)
    end
    
    member
  end

  def strip_tags(doc)
    str=doc.to_s
    str.gsub(/<\/?[^>]*>/, "")
  end

  def min(a, b)
    if a < b
      a
    else
      b
    end
  end
end
