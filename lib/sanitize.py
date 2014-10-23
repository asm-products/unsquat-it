import bleach
from bs4 import BeautifulSoup
import re

allowed_tags = ['a', 'b', 'p', 'i', 'blockquote', 'span', 'ul', 'li', 'ol',
  'strong', 'pre', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'br', 'span']
allowed_attrs = {
  'a': ['href', 'rel'],
}

allowed_tags_media = list(allowed_tags)
allowed_tags_media += ['iframe', 'object', 'embed', 'img']
allowed_attrs_media = dict(allowed_attrs)
allowed_attrs_media.update({
  'iframe': ['src', 'frameborder', 'width', 'height'],
  'img': ['src', 'alt', 'width', 'height'],
  'embed': ['src', 'type', 'width', 'height'],
  'object': ['data', 'type', 'width', 'height'],
})

allowed_styles = ['text-decoration']

# This is exposed to templates as a template method.
# See ui/template_methods.py
def tinymce_valid_elements(media=True):
    if media:
        tags = allowed_tags_media
        attrs = allowed_attrs_media
    else:
        tags = allowed_tags
        attrs = allowed_attrs
    valid_list = []
    for tag in tags:
        elem_attrs = attrs.get(tag)
        if elem_attrs:
            tag += '[%s]' % '|'.join(elem_attrs)
        valid_list.append(tag)
    return ','.join(valid_list)

def linkify(input):
    return bleach.linkify(input)

def html_sanitize(input, media=True):
    if media:
        tags = allowed_tags_media
        attrs = allowed_attrs_media
    else:
        tags = allowed_tags
        attrs = allowed_attrs
    text = bleach.clean(input, tags=tags, attributes=attrs, styles=allowed_styles)
    return text

def html_sanitize_preview(input):
    return bleach.clean(input, tags=[], attributes=[], styles=[], strip=True)

def html_to_text(text):
    soup = BeautifulSoup(text)
    for br in soup.find_all('br'):
        br.string = ' '
    text = soup.get_text()
    return text

def truncate(text, length, ellipsis=True):
    truncated = text[:length]
    if ellipsis and len(text) > length:
        truncated += '...'
    return truncated

def parse_email_reply(mail_text, from_address):
    mail_text = re.compile(r'^On.*?wrote:\s*', re.IGNORECASE | re.MULTILINE | re.DOTALL).sub('', mail_text)
    res = [re.compile(r'From:\s*' + re.escape(from_address), re.IGNORECASE),
           re.compile('<' + re.escape(from_address) + '>', re.IGNORECASE),
           re.compile(r'-+original\s+message-+\s*$', re.IGNORECASE),
           re.compile(r'^from:', re.IGNORECASE),
           re.compile(r'^>')]

    lines = filter(None, [line.rstrip() for line in mail_text.split('\n')])

    result = []
    for line in lines:
        result.append(line)
        for reg_ex in res:
            if reg_ex.search(line):
                result.pop()
                break

    return '\n'.join(filter(None, result))
