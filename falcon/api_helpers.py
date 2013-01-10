import re
from falcon import responders

HTTP_METHODS = (
    'CONNECT',
    'DELETE',
    'GET',
    'HEAD',
    'OPTIONS',
    'POST',
    'PUT',
    'TRACE'
)


def should_ignore_body(status):
    return (status.startswith('204') or
            status.startswith('1') or
            status.startswith('304'))


def set_content_length(env, req, resp):

    # Set Content-Length when given a fully-buffered body or stream length
    if resp.body is not None:
        resp.set_header('Content-Length', str(len(resp.body)))
    elif resp.stream_len is not None:
        resp.set_header('Content-Length', resp.stream_len)
    else:
        resp.set_header('Content-Length', 0)


def compile_uri_template(template):
    """Compile the given URI template string into path and query string
    regex-based templates.

    See also: http://tools.ietf.org/html/rfc6570
    """
    if not isinstance(template, str):
        raise TypeError('uri_template is not a byte string')

    # Convert Level 1 var patterns to equivalent named regex groups
    pattern = re.sub(r'{([a-zA-Z][a-zA-Z_]*)}', r'(?P<\1>[^/]+)', template)
    pattern = r'\A' + pattern + r'\Z'
    return re.compile(pattern, re.IGNORECASE)


def create_http_method_map(handler):
    method_map = {}

    for method in HTTP_METHODS:
        try:
            func = getattr(handler, 'on_' + method.lower())
        except AttributeError:
            # Handler does not implement this method
            pass
        else:
            # Usually expect a method, but any callable will do
            if hasattr(func, '__call__'):
                method_map[method] = func

    # Attach a handler for unsupported HTTP methods
    allowed_methods = method_map.keys()
    func = responders.create_method_not_allowed(allowed_methods)

    for method in HTTP_METHODS:
        if method not in allowed_methods:
            method_map[method] = func

    return method_map