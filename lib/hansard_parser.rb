require 'speech'
require 'mechanize_proxy'
require 'configuration'
require 'debates'
require 'builder_alpha_attributes'
require 'house'
require 'people_image_downloader'
# Using Active Support (part of Ruby on Rails) for Unicode support
require 'activesupport'
require 'rubygems'
require 'log4r'
require 'hansard_page'
require 'hansard_day'

$KCODE = 'u'

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

class HansardParser
  attr_reader :logger
  
  # people passed in initializer have to have their aph_id's set. This can be done by
  # calling PeopleImageDownloader.new.attach_aph_person_ids(people)
  def initialize(people)
    @people = people
    @conf = Configuration.new
    
    # Set up logging
    @logger = Log4r::Logger.new 'HansardParser'
    # Log to both standard out and the file set in configuration.yml
    @logger.add(Log4r::Outputter.stdout)
    @logger.add(Log4r::FileOutputter.new('foo', :filename => @conf.log_path, :trunc => false,
      :formatter => Log4r::PatternFormatter.new(:pattern => "[%l] %d :: %M")))
  end
  
  # Returns the subdirectory where html_cache files for a particular date are stored
  def cache_subdirectory(date, house)
    date.to_s
  end
  
  # Returns HansardDate object for a particular day
  def hansard_day_on_date(date, house)
    agent = MechanizeProxy.new
    agent.cache_subdirectory = cache_subdirectory(date, house)

    # This is the page returned by Parlinfo Search for that day
    url = "http://parlinfo.aph.gov.au/parlInfo/search/display/display.w3p;query=Id:chamber/hansard#{house.representatives? ? "r" : "s"}/#{date}/0000"
    page = agent.get(url)
    tag = page.at('div#content center')
    if tag && tag.inner_html =~ /^Unable to find document/
      nil
    else
      page = agent.click(page.links.text("View/Save XML"))
      HansardDay.new(Hpricot.XML(page.body), logger)
    end
  end
  
  # Parse but only if there is a page that is at "proof" stage
  def parse_date_house_only_in_proof(date, xml_filename, house)
    day = hansard_day_on_date(date, house)
    if day && day.in_proof?
      logger.info "Deleting all cached html for #{date} because that date is in proof stage."
      FileUtils.rm_rf("#{@conf.html_cache_path}/#{cache_subdirectory(date, house)}")
      logger.info "Redownloading pages on #{date}..."
      parse_date_house(date, xml_filename, house)
    end
  end
  
  def parse_date_house(date, xml_filename, house)
    debates = Debates.new(date, house, @logger)
    
    content = false
    day = hansard_day_on_date(date, house)
    if day
      @logger.info "Parsing #{house} speeches for #{date.strftime('%a %d %b %Y')}..."    
      logger.warn "In proof stage" if day.in_proof?
      day.pages.each do |page|
        content = true
        #throw "Unsupported: #{page.full_hansard_title}" unless page.supported? || page.to_skip? || page.not_yet_supported?
        if page
          debates.add_heading(page.hansard_title, page.hansard_subtitle, page.permanent_url)
          speaker = nil
          page.speeches.each do |speech|
            if speech
              # Only change speaker if a speaker name or url was found
              this_speaker = (speech.speakername || speech.aph_id) ? lookup_speaker(speech, date, house) : speaker
              # With interjections the next speech should never be by the person doing the interjection
              speaker = this_speaker unless speech.interjection
        
              debates.add_speech(this_speaker, speech.time, speech.permanent_url, speech.clean_content)
            end
            debates.increment_minor_count
          end
        end
        # This ensures that every sub day page has a different major count which limits the impact
        # of when we start supporting things like written questions, procedurial text, etc..
        debates.increment_major_count      
      end
    else
      @logger.info "Skipping #{house} speeches for #{date.strftime('%a %d %b %Y')} (no data available)"
    end
  
    # Only output the debate file if there's going to be something in it
    debates.output(xml_filename) if content
  end
  
  def lookup_speaker_by_title(speech, date, house)
    # Some sanity checking.
    if speech.speakername =~ /speaker/i && house.senate?
      logger.error "The Speaker is not expected in the Senate"
      return nil
    elsif speech.speakername =~ /president/i && house.representatives?
      logger.error "The President is not expected in the House of Representatives"
      return nil
    elsif speech.speakername =~ /chairman/i && house.representatives?
      logger.error "The Chairman is not expected in the House of Representatives"
      return nil
    end
    
    # Handle speakers where they are referred to by position rather than name
    if speech.speakername =~ /^the speaker/i
      @people.house_speaker(date)
    elsif speech.speakername =~ /^the deputy speaker/i
      @people.deputy_house_speaker(date)
    elsif speech.speakername =~ /^the president/i
      @people.senate_president(date)
    elsif speech.speakername =~ /^(the )?chairman/i || speech.speakername =~ /^the deputy president/i
      # The "Chairman" in the main Senate Hansard is when the Senate is sitting as a committee of the whole Senate.
      # In this case, the "Chairman" is the deputy president. See http://www.aph.gov.au/senate/pubs/briefs/brief06.htm#3
      @people.deputy_senate_president(date)
    # Handle names in brackets
    elsif speech.speakername =~ /^the (deputy speaker|acting deputy president|temporary chairman) \((.*)\)/i
      @people.find_member_by_name_current_on_date(Name.title_first_last($~[2]), date, house)
    end
  end
  
  def lookup_speaker_by_name(speech, date, house)
    throw "speakername can not be nil in lookup_speaker" if speech.speakername.nil?
    
    member = lookup_speaker_by_title(speech, date, house)    
    # If member hasn't already been set then lookup using speakername
    if member.nil?
      name = Name.title_first_last(speech.speakername)
      member = @people.find_member_by_name_current_on_date(name, date, house)
      if member.nil?
        name = Name.last_title_first(speech.speakername)
        member = @people.find_member_by_name_current_on_date(name, date, house)
      end
    end
    member
  end
  
  def lookup_speaker_by_aph_id(speech, date, house)
    person = @people.find_person_by_aph_id(speech.aph_id)
    if person
      # Now find the member for that person who is current on the given date
      @people.find_member_by_name_current_on_date(person.name, date, house)
    else
      logger.error "Can't figure out which person the aph id #{speech.aph_id} belongs to"
      nil
    end
  end
  
  def lookup_speaker(speech, date, house)
    member = lookup_speaker_by_name(speech, date, house)
    if member.nil?
      # Only try to use the aph id if we can't look up by name
      member = lookup_speaker_by_aph_id(speech, date, house) if speech.aph_id
      if member
        # If link is valid use that to look up the member
        logger.error "Determined speaker #{member.person.name.full_name} by link only. Valid name missing."
      end
    end
    
    if member.nil?
      logger.warn "Unknown speaker #{speech.speakername}" unless HansardSpeech.generic_speaker?(speech.speakername)
      member = UnknownSpeaker.new(speech.speakername)
    end
    member
  end
end
