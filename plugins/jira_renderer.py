
import html
from itertools import chain
import mistletoe.html_token as html_token
import mistletoe.block_token
from mistletoe.base_renderer import BaseRenderer
import sys

class JIRARenderer(BaseRenderer):
    """
    JIRA renderer class.

    See mistletoe.base_renderer module for more info.
    """
    def __init__(self, *extras):
        """
        Args:
            extras (list): allows subclasses to add even more custom tokens.
        """
        self.listTokens = []
        tokens = self._tokens_from_module(html_token)
        super().__init__(*chain(tokens, extras))

    def render_strong(self, token):
        template = '*{}*'
        return template.format(self.render_inner(token))

    def render_emphasis(self, token):
        template = '_{}_'
        return template.format(self.render_inner(token))

    def render_inline_code(self, token):
        template = '{{{{{}}}}}'
        return template.format(self.render_inner(token))

    def render_strikethrough(self, token):
        template = '-{}-'
        return template.format(self.render_inner(token))

    def render_image(self, token):
        template = '![{inner}]({src})'
        inner = self.render_inner(token)
        return template.format(src=token.src, inner=inner)

    def render_footnote_image(self, token):
        template = '![{inner}]({src})'        
        maybe_src = self.footnotes.get(token.src.key, '')
        if maybe_src.find('"') != -1:
            src = maybe_src[:maybe_src.index(' "')]
            title = maybe_src[maybe_src.index(' "')+2:-1]
        else:
            src = maybe_src
            title = ''
        inner = self.render_inner(token)
        return template.format(src=token.src, inner=inner)

    def render_link(self, token):
        template = '[{inner}|{target}]'
        target = escape_url(token.target)
        inner = self.render_inner(token)
        return template.format(target=target, inner=inner)

    def render_footnote_link(self, token):
        template = '[{inner}|{target}]'
        raw_target = self.footnotes.get(token.target.key, '')
        target = escape_url(raw_target)
        inner = self.render_inner(token)
        return template.format(target=target, inner=inner)

    def render_auto_link(self, token):
        template = '[{inner}|{target}]'
        target = escape_url(token.target)
        inner = self.render_inner(token)
        return template.format(target=target, inner=inner)

    def render_escape_sequence(self, token):
        return self.render_inner(token)

    @staticmethod
    def render_raw_text(token):
        return html.escape(token.content)

    @staticmethod
    def render_html_span(token):
        return token.content

    def render_heading(self, token):
        template = '\nh{level}. {inner}\n'
        inner = self.render_inner(token)
        return template.format(level=token.level, inner=inner)

    def render_quote(self, token):
        template = 'bq. {inner}\n'
        return template.format(inner=self.render_inner(token))

    def render_paragraph(self, token):
        return '{}\n'.format(self.render_inner(token))

    def render_block_code(self, token):
        # template = '<pre>\n<code{attr}>\n{inner}</code>\n</pre>\n'
        # if token.language:
        #     attr = ' class="{}"'.format('lang-{}'.format(token.language))
        # else:
        #     attr = ''

        template = '{{code:{attr}}}\n{inner}{{code}}\n'
        if token.language:
            attr = '{}'.format(token.language)
        else:
            attr = ''
            
        inner = self.render_inner(token)
        return template.format(attr=attr, inner=inner)

    def render_list(self, token):
        # template = '<{tag}{attr}>\n{inner}</{tag}>\n'
        # if token.start:
        #     tag = 'ol'
        #     attr = ' start="{}"'.format(token.start)
        # else:
        #     tag = 'ul'
        #     attr = ''
        # inner = self.render_inner(token)

        # if token.start:
        #     self.tagType = '#'
            
        # else:
        #     self.tagType = '*'

            
        
        inner = self.render_inner(token)
        return inner

    def render_list_item(self, token):
        
        template = '{prefix} {inner}\n'
        #prefix = self.tagType * self.listLevel
        prefix = ''.join(self.listTokens)
        result = template.format(prefix=prefix, inner=self.render_inner(token))
        return result
        
        
    #return '<li>{}</li>\n'.format(self.render_inner(token))

    def render_inner(self, token):

        #print('###{}###'.format(token))

        if isinstance(token, mistletoe.block_token.List):
            # This needs to be a level
            #self.listLevel += 1
            if token.start:
                self.listTokens.append('#')
            else:
                self.listTokens.append('*')
            
            #print('###{0} {1}###'.format(token, self.listLevel))

        rendered = [self.render(child) for child in token.children]

        if isinstance(token, mistletoe.block_token.List):
            #self.listLevel -= 1
            #print('###EXIT {0} {1}###'.format(token, self.listLevel))
            del (self.listTokens[-1])
        
        
        return ''.join(rendered)
        

    def render_table(self, token):
        # This is actually gross and I wonder if there's a better way to do it.
        #
        # The primary difficulty seems to be passing down alignment options to
        # reach individual cells.
        template = '{inner}\n'
        if token.has_header:
            head_template = '{inner}'
            #print ('hey', token.children)
            header = token.children[0]
            head_inner = self.render_table_row(header, True)
            head_rendered = head_template.format(inner=head_inner)
            token._children = token._children[1:]
            
        else:
            head_rendered = ''
            
        body_template = '{inner}'
        body_inner = self.render_inner(token)
        body_rendered = body_template.format(inner=body_inner)
        return template.format(inner=head_rendered+body_rendered)

    def render_table_row(self, token, is_header=False):
        #template = '<tr>\n{inner}</tr>\n'
        #inner = ''.join([self.render_table_cell(child, is_header)
        #                 for child in token.children])
        if is_header:
            template = '{inner}||\n'
        else:
            template = '{inner}|\n'
            
        inner = ''.join([self.render_table_cell(child, is_header)
                         for child in token.children])

        return template.format(inner=inner)

    def render_table_cell(self, token, in_header=False):
        # template = '<{tag}{attr}>{inner}</{tag}>\n'
        # tag = 'th' if in_header else 'td'
        # if token.align is None:
        #     align = 'left'
        # elif token.align == 0:
        #     align = 'center'
        # elif token.align == 1:
        #     align = 'right'
        # attr = ' align="{}"'.format(align)

        if in_header:
            template = '||{inner}'
        else:
            template = '|{inner}'
        
        inner = self.render_inner(token)
        return template.format(inner=inner)

    @staticmethod
    def render_separator(token):
        return '----\n'

    @staticmethod
    def render_html_block(token):
        return token.content

    def render_document(self, token):
        self.footnotes.update(token.footnotes)
        return self.render_inner(token)

def escape_url(raw):
    """
    Escape urls to prevent code injection craziness. (Hopefully.)
    """
    from urllib.parse import quote
    return quote(raw, safe='/#:')

    
