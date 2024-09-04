from dub import Dub

s = Dub(
    token="dub_Y7q3F4wedjEPHhCloEUAUSb6",
)


res = s.links.create(request={
    "url": "https://google.com"
})

if res is not None:
    # handle response
    print(res)


