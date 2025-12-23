interface Env {
  API_HOST: string
}

export const onRequest: PagesFunction<Env> = async (context) => {
  const apiHost = context.env.API_HOST || 'https://bank-statements-api.onrender.com'
  const url = new URL(context.request.url)
  const apiUrl = `${apiHost}${url.pathname}${url.search}`

  const headers = new Headers(context.request.headers)
  headers.set('Host', new URL(apiHost).host)
  headers.delete('cf-connecting-ip')
  headers.delete('cf-ray')
  headers.delete('cf-visitor')
  headers.delete('cf-ipcountry')

  const init: RequestInit = {
    method: context.request.method,
    headers,
  }

  if (context.request.method !== 'GET' && context.request.method !== 'HEAD') {
    init.body = context.request.body
    init.duplex = 'half'
  }

  const response = await fetch(apiUrl, init)

  const responseHeaders = new Headers(response.headers)
  responseHeaders.delete('content-encoding')
  responseHeaders.delete('content-length')

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  })
}
