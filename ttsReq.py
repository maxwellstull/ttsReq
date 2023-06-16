import requests
import json
import time
from uuid import uuid4



class Requester():
    def __init__(self):
        self.headers = {"accept":"application/json","content-Type": "application/json"}
        self.session = requests.Session()
        self.session.headers = self.headers
        
        self.voices = {
            'WalterWhite':'TM:8afk285jc2gs',
            'BillyMays':'TM:r7as33gptskw'}
        self.jobs = []
        self.to_queue = []
        self.last_tried = 1
    def make_job(self, voice, text, file_dest):
        self.to_queue.append([voice,text,file_dest])
        
    def queue(self, voice, text, file_dest):
        if voice not in self.voices:
            return False
        print("Trying to queue: ", voice)
        payload = {"uuid_idempotency_token":str(uuid4()),"tts_model_token":self.voices[voice],"inference_text":text}
        result = self.session.post(url='https://api.fakeyou.com/tts/inference', data=json.dumps(payload))
        if result.status_code==200:
            print("Queued:", voice)
            job_token = result.json()["inference_job_token"]
            self.jobs.append([job_token, file_dest])
            return True
        if result.status_code==429:
            print("Cant queue: ", voice)
            self.to_queue.append([voice,text,file_dest])
        return False
    
    def poll_job_progress(self):
        while len(self.jobs) > 0 or len(self.to_queue) > 0:
            to_remove = []
            for _job in self.jobs:
                job_token = _job[0]
                
                result = self.session.get("https://api.fakeyou.com/tts/job/{tok}".format(tok=job_token))
                result_dict = json.loads(result.text)
                if result_dict['state']['status'] == 'complete_success':
                    path = 'https://storage.googleapis.com/vocodes-public' + result_dict['state']['maybe_public_bucket_wav_audio_path']
                    self.save_file(_job[1], path)
                    to_remove.append(_job)
            print(len(self.jobs),"jobs in queue.",len(self.to_queue)," jobs awaiting queue.")
            for job in to_remove:
                self.jobs.remove(job)
                if len(self.to_queue) > 0:
                    to_q = self.to_queue[0]
                    self.to_queue.pop(0)
                    self.make_job(to_q[0],to_q[1],to_q[2])
            if (len(self.jobs) == 0 or self.last_tried <= 0) and len(self.to_queue) > 0:

                for i in range(0,1):
                    to_q = self.to_queue[0]
                    self.to_queue.pop(0)
                    self.queue(to_q[0],to_q[1],to_q[2])
                self.last_tried = 1
            self.last_tried = self.last_tried-1
            time.sleep(5)

    
    
    
    def save_file(self,title, path):
        r = requests.get(path)
        open("{title}".format(title=title),'wb').write(r.content)