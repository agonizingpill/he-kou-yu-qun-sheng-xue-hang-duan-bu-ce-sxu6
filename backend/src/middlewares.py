import time,uuid,logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
class RequestTrace(BaseHTTPMiddleware):
    async def dispatch(self,request,call_next):
        rid=uuid.uuid4().hex[:12];start=time.monotonic()
        response=await call_next(request)
        response.headers['X-Request-Id']=rid
        logging.getLogger('estuary.access').info('%s %s %s %.3f',rid,request.url.path,response.status_code,time.monotonic()-start)
        return response
class BurstLimit(BaseHTTPMiddleware):
    buckets={}
    async def dispatch(self,request,call_next):
        key=request.client.host;now=time.monotonic()
        times=[v for v in self.buckets.get(key,[]) if now-v<10]
        if len(times)>=500:return JSONResponse({'detail':'操作过密，请稍候重试'},status_code=429)
        self.buckets[key]=times+[now]
        return await call_next(request)
