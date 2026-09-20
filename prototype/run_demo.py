import uvicorn
import argparse
import getpass
import os

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument('--prompt-key',action='store_true',help='Read a hidden runtime secret; never save it')
    parser.add_argument('--port',type=int,default=8000)
    args=parser.parse_args()
    if args.prompt_key:
        os.environ['GOOGLE_API_KEY']=getpass.getpass('Google API key (hidden, runtime only): ')
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=args.port, reload=False, access_log=False)
