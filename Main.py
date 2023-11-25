# Copyright RoomFinder 2023 @
#
#     All rights remain in the hands of Tomer Hambra,
#     Ilay Nadler, and Roy Sigman. Any violation of this Copyright 
#     will cost in a lawsuit.
#  
#     https://roomfinder.streamlit.app


import utils, time, asyncio, httpx


def run():
  
  while True:
    url = 'https://beitbiram.iscool.co.il/default.aspx'
    if not url == '':
      maker = utils.Maker(url, utils.Maker.schoolids[url], utils.Maker.control[url])
      unavailable_site_error = False
      try: asyncio.run(maker.download_htmls(url, maker.schoolid, maker.control))
      except httpx.ConnectTimeout:
        unavailable_site_error = True
      
      
      if not unavailable_site_error: 
        maker.run()
    time.sleep(300)
    
    
if __name__ == '__main__':
  run()
    # :: NOTE ::    HELP WITH REWORK    :: NOTE :: 