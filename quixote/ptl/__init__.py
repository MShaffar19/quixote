'''
PTL: Python Template Language
=============================

Introduction
------------

PTL is the templating language used by Quixote.  Most web templating
languages embed a real programming language in HTML, but PTL inverts
this model by merely tweaking Python to make it easier to generate
HTML pages (or other forms of text).  In other words, PTL is basically
Python with a novel way to specify function return values.

Specifically, a PTL template is designated by inserting a ``[plain]``
or ``[html]`` modifier after the function name.  The value of
expressions inside templates are kept, not discarded.  If the type is
``[html]`` then non-literal strings are passed through a function that
escapes HTML special characters.


Plain text templates
--------------------

Here's a sample plain text template::

    def foo [plain] (x, y = 5):
        "This is a chunk of static text."
        greeting = "hello world" # statement, no PTL output
        print 'Input values:', x, y
        z = x + y
        """You can plug in variables like x (%s)
    in a variety of ways.""" % x

        "\n\n"
        "Whitespace is important in generated text.\n"
        "z = "; z
        ", but y is "
        y
        "."

Obviously, templates can't have docstrings, but otherwise they follow
Python's syntactic rules: indentation indicates scoping, single-quoted
and triple-quoted strings can be used, the same rules for continuing
lines apply, and so forth.  PTL also follows all the expected semantics
of normal Python code: so templates can have parameters, and the
parameters can have default values, be treated as keyword arguments,
etc.

The difference between a template and a regular Python function is that
inside a template the result of expressions are saved as the return
value of that template.  Look at the first part of the example again::

    def foo [plain] (x, y = 5):
        "This is a chunk of static text."
        greeting = "hello world" # statement, no PTL output
        print 'Input values:', x, y
        z = x + y
        """You can plug in variables like x (%s)
    in a variety of ways.""" % x

Calling this template with ``foo(1, 2)`` results in the following
string::

    This is a chunk of static text.You can plug in variables like x (1)
    in a variety of ways.

Normally when Python evaluates expressions inside functions, it just
discards their values, but in a ``[plain]`` PTL template the value is
converted to a string using ``str()`` and appended to the template's
return value.  There's a single exception to this rule: ``None`` is the
only value that's ever ignored, adding nothing to the output.  (If this
weren't the case, calling methods or functions that return ``None``
would require assigning their value to a variable.  You'd have to write
``dummy = list.sort()`` in PTL code, which would be strange and
confusing.)

The initial string in a template isn't treated as a docstring, but is
just incorporated in the generated output; therefore, templates can't
have docstrings.  No whitespace is ever automatically added to the
output, resulting in ``...text.You can ...`` from the example.  You'd
have to add an extra space to one of the string literals to correct
this.

The assignment to the ``greeting`` local variable is a statement, not an
expression, so it doesn't return a value and produces no output.  The
output from the ``print`` statement will be printed as usual, but won't
go into the string generated by the template.  Quixote directs standard
output into Quixote's debugging log; if you're using PTL on its own, you
should consider doing something similar.  ``print`` should never be used
to generate output returned to the browser, only for adding debugging
traces to a template.

Inside templates, you can use all of Python's control-flow statements::

    def numbers [plain] (n):
        for i in range(n):
            i
            " " # PTL does not add any whitespace

Calling ``numbers(5)`` will return the string ``"1 2 3 4 5 "``.  You can
also have conditional logic or exception blocks::

    def international_hello [plain] (language):
        if language == "english":
            "hello"
        elif language == "french":
            "bonjour"
        else:
            raise ValueError, "I don't speak %s" % language


HTML templates
--------------

Since PTL is usually used to generate HTML documents, an ``[html]``
template type has been provided to make generating HTML easier.  

A common error when generating HTML is to grab data from the browser
or from a database and incorporate the contents without escaping
special characters such as '<' and '&'.  This leads to a class of
security bugs called "cross-site scripting" bugs, where a hostile user
can insert arbitrary HTML in your site's output that can link to other
sites or contain JavaScript code that does something nasty (say,
popping up 10,000 browser windows).

Such bugs occur because it's easy to forget to HTML-escape a string,
and forgetting it in just one location is enough to open a hole.  PTL
offers a solution to this problem by being able to escape strings
automatically when generating HTML output, at the cost of slightly
diminished performance (a few percent).

Here's how this feature works.  PTL defines a class called
``htmltext`` that represents a string that's already been HTML-escaped
and can be safely sent to the client.  The function ``htmlescape(string)``
is used to escape data, and it always returns an ``htmltext``
instance.  It does nothing if the argument is already ``htmltext``.

If a template function is declared ``[html]`` instead of ``[text]``
then two things happen.  First, all literal strings in the function
become instances of ``htmltext`` instead of Python's ``str``.  Second,
the values of expressions are passed through ``htmlescape()`` instead
of ``str()``.

``htmltext`` type is like the ``str`` type except that operations
combining strings and ``htmltext`` instances will result in the string
being passed through ``htmlescape()``.  For example::

    >>> from quixote.html import htmltext
    >>> htmltext('a') + 'b'
    <htmltext 'ab'>
    >>> 'a' + htmltext('b')
    <htmltext 'ab'>
    >>> htmltext('a%s') % 'b'
    <htmltext 'ab'>
    >>> response = 'green eggs & ham'
    >>> htmltext('The response was: %s') % response
    <htmltext 'The response was: green eggs &amp; ham'>

Note that calling ``str()`` strips the ``htmltext`` type and should be
avoided since it usually results in characters being escaped more than
once.  While ``htmltext`` behaves much like a regular string, it is
sometimes necessary to insert a ``str()`` inside a template in order
to obtain a genuine string.  For example, the ``re`` module requires
genuine strings.  We have found that explicit calls to ``str()`` can
often be avoided by splitting some code out of the template into a
helper function written in regular Python.

It is also recommended that the ``htmltext`` constructor be used as
sparingly as possible.  The reason is that when using the htmltext
feature of PTL, explicit calls to ``htmltext`` become the most likely
source of cross-site scripting holes.  Calling ``htmltext`` is like
saying "I am absolutely sure this piece of data cannot contain malicious
HTML code injected by a user.  Don't escape HTML special characters
because I want them."

Note that literal strings in template functions declared with
``[html]`` are htmltext instances, and therefore won't be escaped.
You'll only need to use ``htmltext`` when HTML markup comes from
outside the template.  For example, if you want to include a file
containing HTML::

    def output_file [html] ():
        '<html><body>' # does not get escaped
        htmltext(open("myfile.html").read())
        '</body></html>'

In the common case, templates won't be dealing with HTML markup from
external sources, so you can write straightforward code.  Consider
this function to generate the contents of the ``HEAD`` element::

    def meta_tags [html] (title, description):
        '<title>%s</title>' % title
        '<meta name="description" content="%s">\n' % description

There are no calls to ``htmlescape()`` at all, but string literals
such as ``<title>%s</title>`` have all be turned into ``htmltext``
instances, so the string variables will be automatically escaped::

    >>> t.meta_tags('Catalog', 'A catalog of our cool products')
    <htmltext '<title>Catalog</title>
      <meta name="description" content="A catalog of our cool products">\n'>
    >>> t.meta_tags('Dissertation on <HEAD>', 
    ...             'Discusses the "LINK" and "META" tags')
    <htmltext '<title>Dissertation on &lt;HEAD&gt;</title>
      <meta name="description" 
       content="Discusses the &quot;LINK&quot; and &quot;META&quot; tags">\n'>
    >>>

Note how the title and description have had HTML-escaping applied to them.
(The output has been manually pretty-printed to be more readable.)

Once you start using ``htmltext`` in one of your templates, mixing
plain and HTML templates is tricky because of ``htmltext``'s automatic
escaping; plain templates that generate HTML tags will be
double-escaped.  One approach is to just use HTML templates throughout
your application.  Alternatively you can use ``str()`` to convert
``htmltext`` instances to regular Python strings; just be sure the
resulting string isn't HTML-escaped again.

Two implementations of ``htmltext`` are provided, one written in pure
Python and a second one implemented as a C extension.  Both versions
have seen production use.  


PTL modules
-----------

PTL templates are kept in files with the extension .ptl.  Like
Python files, they are byte-compiled and the byte-code is written to
a compiled file with the extension ``.pyc``.  Since vanilla Python
doesn't know anything about PTL, this package provides a function
that compiles a package containing PTL files.  To use it, add these
lines to the __init__ module of the package:

    from quixote.ptl import compile_package
    compile_package(__path__)

'''
from quixote.ptl.ptl_compile import compile_package
