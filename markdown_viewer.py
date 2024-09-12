import tkinter as tk
import markdown
import webbrowser
import os

# Define a standard file path
STANDARD_FILE_PATH = os.path.join(os.getcwd(), 'rendered_markdown.html')

class MarkdownViewer:
    def __init__(self, root, text):
        self.root = root
        self.text = text
        self.setup_ui()

    def setup_ui(self):
        self.render_markdown()

    def render_markdown(self):
        extensions = [
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc'
        ]

        md = markdown.Markdown(extensions=extensions)
        html_content = md.convert(self.text)

        # Custom CSS and JavaScript to enhance rendering
        custom_css = """
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f4f4;
                color: #333;
                margin: 20px;
            }
            .markdown-body {
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            pre {
                background-color: #2d2d2d;
                color: #fff;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
            }
            code {
                background-color: #f0f0f0;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: 'Courier New', Courier, monospace;
            }
            pre code {
                background-color: transparent;
                padding: 0;
            }
            .codehilite .hll {
                background-color: #444;
            }
            .codehilite .c { color: #999; } /* Comment */
            .codehilite .k { color: #f92672; } /* Keyword */
            .codehilite .o { color: #ae81ff; } /* Operator */
            .codehilite .cm { color: #999; } /* Comment.Multiline */
            .codehilite .cp { color: #f92672; } /* Comment.Preproc */
            .codehilite .c1 { color: #999; } /* Comment.Single */
            .codehilite .cs { color: #999; } /* Comment.Special */
            .codehilite .gd { color: #f92672; } /* Generic.Deleted */
            .codehilite .ge { font-style: italic; } /* Generic.Emph */
            .codehilite .gr { color: #f92672; } /* Generic.Error */
            .codehilite .gh { color: #ae81ff; } /* Generic.Heading */
            .codehilite .gi { color: #a6e22e; } /* Generic.Inserted */
            .codehilite .go { color: #66d9ef; } /* Generic.Output */
            .codehilite .gp { color: #f92672; } /* Generic.Prompt */
            .codehilite .gs { font-weight: bold; } /* Generic.Strong */
            .codehilite .gu { color: #ae81ff; } /* Generic.Subheading */
            .codehilite .gt { color: #f92672; } /* Generic.Traceback */
            .codehilite .kc { color: #f92672; } /* Keyword.Constant */
            .codehilite .kd { color: #f92672; } /* Keyword.Declaration */
            .codehilite .kn { color: #f92672; } /* Keyword.Namespace */
            .codehilite .kp { color: #f92672; } /* Keyword.Pseudo */
            .codehilite .kr { color: #f92672; } /* Keyword.Reserved */
            .codehilite .kt { color: #f92672; } /* Keyword.Type */
            .codehilite .m { color: #ae81ff; } /* Literal.Number */
            .codehilite .s { color: #a6e22e; } /* Literal.String */
            .codehilite .na { color: #a6e22e; } /* Name.Attribute */
            .codehilite .nb { color: #f92672; } /* Name.Builtin */
            .codehilite .nc { color: #a6e22e; } /* Name.Class */
            .codehilite .no { color: #f92672; } /* Name.Constant */
            .codehilite .nd { color: #a6e22e; } /* Name.Decorator */
            .codehilite .ni { color: #ae81ff; } /* Name.Entity */
            .codehilite .ne { color: #f92672; } /* Name.Exception */
            .codehilite .nf { color: #a6e22e; } /* Name.Function */
            .codehilite .nl { color: #f92672; } /* Name.Label */
            .codehilite .nn { color: #f92672; } /* Name.Namespace */
            .codehilite .nx { color: #a6e22e; } /* Name.Other */
            .codehilite .py { color: #f92672; } /* Name.Property */
            .codehilite .nt { color: #f92672; } /* Name.Tag */
            .codehilite .nv { color: #f92672; } /* Name.Variable */
            .codehilite .ow { color: #f92672; } /* Operator.Word */
            .codehilite .w { color: #f8f8f2; } /* Text.Whitespace */
            .codehilite .mf { color: #ae81ff; } /* Literal.Number.Float */
            .codehilite .mh { color: #ae81ff; } /* Literal.Number.Hex */
            .codehilite .mi { color: #ae81ff; } /* Literal.Number.Integer */
            .codehilite .mo { color: #ae81ff; } /* Literal.Number.Oct */
            .codehilite .sb { color: #a6e22e; } /* Literal.String.Backtick */
            .codehilite .sc { color: #a6e22e; } /* Literal.String.Char */
            .codehilite .sd { color: #a6e22e; } /* Literal.String.Doc */
            .codehilite .s2 { color: #a6e22e; } /* Literal.String.Double */
            .codehilite .se { color: #ae81ff; } /* Literal.String.Escape */
            .codehilite .sh { color: #a6e22e; } /* Literal.String.Heredoc */
            .codehilite .si { color: #a6e22e; } /* Literal.String.Interpol */
            .codehilite .sx { color: #a6e22e; } /* Literal.String.Other */
            .codehilite .sr { color: #a6e22e; } /* Literal.String.Regex */
            .codehilite .s1 { color: #a6e22e; } /* Literal.String.Single */
            .codehilite .ss { color: #a6e22e; } /* Literal.String.Symbol */
            .codehilite .bp { color: #f92672; } /* Name.Builtin.Pseudo */
            .codehilite .vc { color: #f92672; } /* Name.Variable.Class */
            .codehilite .vg { color: #f92672; } /* Name.Variable.Global */
            .codehilite .vi { color: #f92672; } /* Name.Variable.Instance */
            .codehilite .il { color: #ae81ff; } /* Literal.Number.Integer.Long */
        </style>
        """

        custom_js = """
        <script>
            document.addEventListener('DOMContentLoaded', (event) => {
                document.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightBlock(block);
                });

                // Initialize MathJax
                MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
            });
        </script>
        """

        # Combine HTML content with custom CSS and JavaScript
        html_content = f"""
        <html>
        <head>
            {custom_css}
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.10/highlight.min.js"></script>
            <script type="text/javascript" async
                src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML">
            </script>
            <script type="text/x-mathjax-config">
                MathJax.Hub.Config({{
                    tex2jax: {{
                        inlineMath: [['$','$'], ['$$','$$']],
                        processEscapes: true
                    }}
                }});
            </script>
            {custom_js}
        </head>
        <body class="markdown-body">
        {html_content}
        </body>
        </html>
        """

        # Write the HTML content to the standard file path
        with open(STANDARD_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Open the standard HTML file in the default web browser
        webbrowser.open('file://' + STANDARD_FILE_PATH)

def show_markdown_viewer(root, text):
    MarkdownViewer(root, text)