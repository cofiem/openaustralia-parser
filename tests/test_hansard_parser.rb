$:.unshift "#{File.dirname(__FILE__)}/../lib"

require 'test/unit'
require 'hansard_parser'
require 'rubygems'
require 'hpricot'

class TestHansardParser < Test::Unit::TestCase
  def test_make_motions_and_quotes_italic
    doc = Hpricot('<p>I move:</p><div class="motion"><p>Some text</p></div>')
    HansardParser.make_motions_and_quotes_italic(doc)
    assert_equal('<p>I move:</p><p class="italic">Some text</p>', doc.to_s)
  end
  
  def test_remove_subspeech_tags
    doc = Hpricot('<div class="subspeech0"><p>Some Text</p></div><div class="subspeech0"><p>Some Other Text</p></div>')
    HansardParser.remove_subspeech_tags(doc)
    assert_equal('<p>Some Text</p><p>Some Other Text</p>', doc.to_s)
  end
  
  def test_fix_links_relative_link
    doc = Hpricot('<p>The <a href="foo.html">Link Text</a> Some Text</p>')
    HansardParser.fix_links("http://website/bar/blah.html", doc)
    assert_equal('<p>The <a href="http://website/bar/foo.html">Link Text</a> Some Text</p>', doc.to_s)
  end
  
  def test_fix_links_absolute_link
    doc = Hpricot('<p>The <a href="http://anothersite/foo.html">Link Text</a> Some Text</p>')
    HansardParser.fix_links("http://website/bar/blah.html", doc)
    assert_equal('<p>The <a href="http://anothersite/foo.html">Link Text</a> Some Text</p>', doc.to_s)
  end
  
  def test_fix_links_empty_a_tag
    doc = Hpricot('<p>The <a>Link Text</a> Some Text</p>')
    HansardParser.fix_links("http://website/bar/blah.html", doc)
    assert_equal('<p>The Link Text Some Text</p>', doc.to_s)
  end
  
  def test_make_amendments_italic
    doc = Hpricot('<div class="amendments"><div class="amendment0"><p class="paraParlAmend">Some Text</p></div><div class="amendment1"><p class="paraParlAmend">Some more text</p></div></div>')
    HansardParser.make_amendments_italic(doc)
    assert_equal('<p class="italic">Some Text</p><p class="italic">Some more text</p>', doc.to_s)
  end
end