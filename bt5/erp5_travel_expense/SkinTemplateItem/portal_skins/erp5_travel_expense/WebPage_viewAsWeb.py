if REQUEST is None:
  REQUEST = context.REQUEST
if response is None:
  response = REQUEST.RESPONSE

web_page = context

if REQUEST.getHeader('If-Modified-Since', '') == web_page.getModificationDate().rfc822():
  response.setStatus(304)
  return ""

portal_type = web_page.getPortalType()
web_content = web_page.getTextContent()

# set headers depending on type of script
if (portal_type == "Web Script"):
  response.setHeader('Content-Type', 'application/javascript')

elif (portal_type == "Web Style"):
  response.setHeader('Content-Type', 'text/css')

elif (portal_type == "Web Manifest"):
  response.setHeader('Content-Type', 'text/cache-manifest')

else:
  if (mapping_dict is not None):
    web_content = web_page.TextDocument_substituteTextContent(web_content, mapping_dict=mapping_dict)
  # Do not allow to put inside an iframe
  # response.setHeader("X-Frame-Options", "SAMEORIGIN")
  response.setHeader("X-Content-Type-Options", "nosniff")

  # Only fetch code (html, js, css, image) and data from this ERP5, to prevent any data leak as the web site do not control the gadget's code
  response.setHeader("Content-Security-Policy", "default-src 'none'; img-src 'self' blob: data:; media-src 'self'; connect-src * 'self' mail.tiolive.com; script-src 'self' 'unsafe-eval' cdn.jsdelivr.net cdnjs.cloudflare.com; font-src netdna.bootstrapcdn.com; style-src 'self' cdn.jsdelivr.net netdna.bootstrapcdn.com cdnjs.cloudflare.com 'unsafe-inline' data:; frame-src 'self' data:")

  response.setHeader('Content-Type', 'text/html')

return web_content
