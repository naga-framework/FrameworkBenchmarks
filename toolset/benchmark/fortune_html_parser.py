# -*- coding: utf-8
import re
from HTMLParser import HTMLParser
from difflib import unified_diff

class FortuneHTMLParser(HTMLParser):
  body = []

  valid = '''<!doctype html><html>
<head><title>Fortunes</title></head>
<body><table>
<tr><th>id</th><th>message</th></tr>
<tr><td>11</td><td>&lt;script&gt;alert(&quot;This should not be displayed in a browser alert box.&quot;);&lt;/script&gt;</td></tr>
<tr><td>4</td><td>A bad random number generator: 1, 1, 1, 1, 1, 4.33e+67, 1, 1, 1</td></tr>
<tr><td>5</td><td>A computer program does what you tell it to do, not what you want it to do.</td></tr>
<tr><td>2</td><td>A computer scientist is someone who fixes things that aren&apos;t broken.</td></tr>
<tr><td>8</td><td>A list is only as strong as its weakest link. — Donald Knuth</td></tr>
<tr><td>0</td><td>Additional fortune added at request time.</td></tr>
<tr><td>3</td><td>After enough decimal places, nobody gives a damn.</td></tr>
<tr><td>7</td><td>Any program that runs right is obsolete.</td></tr>
<tr><td>10</td><td>Computers make very fast, very accurate mistakes.</td></tr>
<tr><td>6</td><td>Emacs is a nice operating system, but I prefer UNIX. — Tom Christaensen</td></tr>
<tr><td>9</td><td>Feature: A bug with seniority.</td></tr>
<tr><td>1</td><td>fortune: No such file or directory</td></tr>
<tr><td>12</td><td>フレームワークのベンチマーク</td></tr>
</table></body></html>'''

  # Is called when a doctype or other such tag is read in.
  # For our purposes, we assume this is only going to be
  # "DOCTYPE html", so we will surround it with "<!" and ">".
  def handle_decl(self, decl):
    # The spec says that for HTML this is case insensitive,
    # and since we did not specify xml compliance (where 
    # incorrect casing would throw a syntax error), we must
    # allow all casings. We will lower for our normalization.
    self.body.append("<!{d}>".format(d=decl.lower()))

  # This is called when an HTML character is parsed (i.e. 
  # &quot;). There are a number of issues to be resolved 
  # here. For instance, some tests choose to leave the
  # "+" character as-is, which should be fine as far as
  # character escaping goes, but others choose to use the
  # character reference of "&#43;", which is also fine.
  # Therefore, this method looks for all possible character
  # references and normalizes them so that we can 
  # validate the input against a single valid spec string.
  # Another example problem: "&quot;" is valid, but so is
  # "&#34;"
  def handle_charref(self, name):
    val = name.lower()
    # "&#34;" is a valid escaping, but we are normalizing
    # it so that our final parse can just be checked for
    # equality.
    if val == "34" or val == "034" or val == "x22":
      # Append our normalized entity reference to our body.
      self.body.append("&quot;")
    # "&#39;" is a valid escaping of "-", but it is not
    # required, so we normalize for equality checking.
    if val == "39" or val == "039" or val == "x27":
      self.body.append("&apos;")
    # Again, "&#43;" is a valid escaping of the "+", but
    # it is not required, so we need to normalize for out
    # final parse and equality check.
    if val == "43" or val == "043" or val == "x2b":
      self.body.append("+")
    # Again, "&#62;" is a valid escaping of ">", but we
    # need to normalize to "&gt;" for equality checking.
    if val == "62" or val == "062" or val == "x3e":
      self.body.append("&gt;")
    # Again, "&#60;" is a valid escaping of "<", but we
    # need to normalize to "&lt;" for equality checking.
    if val == "60" or val == "060" or val == "x3c":
      self.body.append("&lt;")
    # Not sure why some are escaping '/'
    if val == "47" or val == "047" or val == "x2f":
      self.body.append("/")

  def handle_entityref(self, name):
    # Again, "&mdash;" is a valid escaping of "—", but we
    # need to normalize to "—" for equality checking.
    if name == "mdash":
      self.body.append("—")
    else:  
      self.body.append("&{n};".format(n=name))

  # This is called every time a tag is opened. We append
  # each one wrapped in "<" and ">".
  def handle_starttag(self, tag, attrs):
    self.body.append("<{t}>".format(t=tag))
    
    # Append a newline after the <table> and <html>
    if tag.lower() == 'table' or tag.lower() == 'html':
      self.body.append("\n")

  # This is called whenever data is presented inside of a
  # start and end tag. Generally, this will only ever be
  # the contents inside of "<td>" and "</td>", but there
  # are also the "<title>" and "</title>" tags.
  def handle_data (self, data):
    if data.strip() != '':
      # After a LOT of debate, these are now considered
      # valid in data. The reason for this approach is
      # because a few tests use tools which determine
      # at compile time whether or not a string needs
      # a given type of html escaping, and our fortune
      # test has apostrophes and quotes in html data
      # rather than as an html attribute etc.
      # example:
      # <td>A computer scientist is someone who fixes things that aren't broken.</td>
      # Semanticly, that apostrophe does not NEED to
      # be escaped. The same is currently true for our
      # quotes.
      # In fact, in data (read: between two html tags)
      # even the '>' need not be replaced as long as
      # the '<' are all escaped.
      # We replace them with their escapings here in
      # order to have a noramlized string for equality
      # comparison at the end.
      data = data.replace('\'', '&apos;')
      data = data.replace('"', '&quot;')
      data = data.replace('>', '&gt;')

      self.body.append("{d}".format(d=data))

  # This is called every time a tag is closed. We append
  # each one wrapped in "</" and ">".
  def handle_endtag(self, tag):
    self.body.append("</{t}>".format(t=tag))

    # Append a newline after each </tr> and </head>
    if tag.lower() == 'tr' or tag.lower() == 'head':
      self.body.append("\n")

  # Returns whether the HTML input parsed by this parser
  # is valid against our known "fortune" spec.
  # The parsed data in 'body' is joined on empty strings
  # and checked for equality against our spec.
  def isValidFortune(self, out):
    body = ''.join(self.body)
    same = self.valid == body
    diff_lines = []
    if not same:
      out.write("Oh no! I compared %s\n\n\nto.....%s" % (self.valid, body))
      out.write("Fortune invalid. Diff following:\n")
      headers_left = 3
      for line in unified_diff(self.valid.split('\n'), body.split('\n'), fromfile='Valid', tofile='Response', n=0):
        diff_lines.append(line)
        out.write(line)
        headers_left -= 1
        if headers_left <= 0:
          out.write('\n')
    return (same, diff_lines)
