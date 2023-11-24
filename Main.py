import utils, time, csv


def run():
  urls = {
    '':'',
    'Reali - Beit Biram':'https://beitbiram.iscool.co.il/default.aspx', 
    'Rabinky':'https://rabinky.iscool.co.il/default.aspx'
  }
  schoolids = {
    'https://beitbiram.iscool.co.il/default.aspx':7126,
    'https://rabinky.iscool.co.il/default.aspx':7121
  }
  control = {
    'https://beitbiram.iscool.co.il/default.aspx':'8',
    'https://rabinky.iscool.co.il/default.aspx':'8'
  }
  while True:
    for url in urls.values():
      if not url == '':
        maker = Maker(url, schoolids[url], control[url])
        unavailable_site_error = False
        try:
          htmls = asyncio.run(maker.download_htmls())
        except httpx.ConnectTimeout:
          unavailable_site_error = True
        
        
        if not unavailable_site_error: 
          with open(f'{schoolid}\\res.csv') as f:
            for day in range(7):
              for hour in range(14):
                rooms = sorted(get_available_classes_on_date(htmls.values(), day, hour))
                f.write(rooms)
                f.write('\n')
    time.sleep(200)
    
    
    
    # :: NOTE ::    HELP WITH REWORK    :: NOTE :: 