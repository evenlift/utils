import csv
import pafy
import imageio
# from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import cv2 as cv
import time
import sys
import os

class interval:
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __repr__(self):
        return "s: {} e: {}".format(self.start, self.end)

    def __str__(self):
        return "s: {} e: {}".format(self.start, self.end)

class videoRequest:
    def __init__(self):
        self.id = ""
        self.topSnaps = []
        self.bottomSnaps = []
        self.intervals = []
        self.category = ""

    def populate(self, id,  intervals, topSnaps, bottomSnaps, category):
        self.id = id
        self.topSnaps = self.parseInstants(topSnaps)
        self.bottomSnaps = self.parseInstants(bottomSnaps)
        self.intervals = self.parseIntervals(intervals)
        self.category = category

    def parseInstants(self, instants):
        instant_list = []
        instants = instants.split(",")

        for i in instants:
            instant_list.append(self.parseInstant(i))

        return instant_list


    def parseInstant(self, instant):
        ret = 0.0
        tmp = instant.split(":")

        if len(tmp) == 2:
            ret += float(tmp[0].strip()) * 60
            ret += float(tmp[1].strip())
        elif len(tmp) == 3:
            ret += float(tmp[0].strip()) * 3600
            ret += float(tmp[1].strip()) * 60
            ret += float(tmp[2].strip())

        return ret


    def parseIntervals(self, intervals):
        interval_list = []
        intervals = intervals.split(",")

        for i in intervals:
            i = i.split("-")

            if len(i) == 1:
                continue

            tmp = interval(self.parseInstant(i[0].strip()), self.parseInstant(i[1].strip()))
            interval_list.append(tmp)

        return interval_list


def createVideoRequest():
    return videoRequest()        

class clipGetter:

    def __init__(self, video_directory="./pygym_videos", request_sheet="video_list.csv", target_image_directory="images", SECONDS_BETWEEN_STILLS=0.5, include_top_and_bottom=False):
        self.video_directory = video_directory
        self.request_sheet = request_sheet
        self.video_requests = []
        self.video_dict = {}
        self.target_image_directory = target_image_directory
        self.SECONDS_BETWEEN_STILLS = SECONDS_BETWEEN_STILLS
        self.include_top_and_bottom = include_top_and_bottom
        self.parse_existing_vids()

    def parse_existing_vids(self):
        os.chdir(self.video_directory)
        for x in os.listdir():
            if os.path.isdir(x):
                print("There's a directory in your video directory.  Weird?")
                continue
            else:
                filename, file_ext = os.path.splitext(x)
                self.video_dict[filename] = x
        os.chdir("..")

    def parseRequestSheet(self):
        video_requests = []
        with open(self.request_sheet, "r") as csvfile:
            rowReader = csv.reader(csvfile)

            for idx, row in enumerate(rowReader):
                try:
                    tmp = createVideoRequest()
                    if idx == 0:
                        continue
                    tmp.populate(row[0], row[1], row[2], row[3], row[4])
                    video_requests.append(tmp)
                except ValueError as e:
                    print("Formatting error with row {}, video ID: {}, error: {}".format(idx + 1, row[0], e))
                    raise 

        self.video_requests = video_requests

    def fillRequests(self):
    
        for r in self.video_requests:
            if r.id not in self.video_dict:

                for _ in range(5):
                    try:
                        self.get_video(r.id)
                        self.parse_existing_vids()
                        break
                    except Exception as e:
                        print(r.id + "  " + str(e)) 
                        self.video_requests.append(r)

            if self.include_top_and_bottom:
                self.getStills(r.id, self.target_image_directory + "\\" + r.category + "\\top", r.topSnaps)
                self.getStills(r.id, self.target_image_directory + "\\" + r.category + "\\bottom", r.bottomSnaps)

            self.getStillsFromIntervals(r.id, self.target_image_directory + "\\" + r.category, r.intervals)

    def getStills(self, videoID, imagesPath, instants):
        #Check if directory exists.  If not, make it, man
        cwd = os.getcwd()
        try:
            os.chdir(imagesPath)
            os.chdir(cwd)
        except FileNotFoundError as e:
            print("Creating image folder {}".format(imagesPath))
            os.chdir(cwd)
            os.makedirs(imagesPath)

        cap = cv.VideoCapture(self.video_directory + "\\" + videoID + ".mp4")
        count = 0
        fps = cap.get(cv.CAP_PROP_FPS)
            
        for i in instants:
            cap.set(cv.CAP_PROP_POS_FRAMES, i * fps)
            ret, frame = cap.read()
            filepath = imagesPath + "\\" + videoID + str(count) + ".jpg"

            ret = cv.imwrite(filepath, frame)
            if not ret:
                print("Failed to write image.  ID: {}  Instant: {}".format(videoID, i))             

            count += 1

        cap.release()

    def getStillsFromIntervals(self, videoID, imagesPath, intervals):
        # Checking that all intervals start after the previous one is finished
        if not self.validIntervals(intervals):
            print("Intervals for {} are not valid.  Stopping process.".format(videoID))
            sys.exit()

        #Check if directory exists.  If not, well, make it, man
        cwd = os.getcwd()
        try:
            os.chdir(imagesPath)
            os.chdir(cwd)
        except FileNotFoundError as e:
            print("Creating image folder {}".format(imagesPath))
            os.chdir(cwd)
            os.makedirs(imagesPath)

        cap = cv.VideoCapture(self.video_directory + "\\" + videoID + ".mp4")
        fps = cap.get(cv.CAP_PROP_FPS) 
        count = 0

        for i in intervals:
            
            cap.set(cv.CAP_PROP_POS_FRAMES, i.start * fps)

            for j in range(int((i.end - i.start) * fps)):
                ret, frame = cap.read()
                if not ret:
                    print("Error reading {}.  Exiting.".format(videoID))
                    raise

                frame_delta = fps * self.SECONDS_BETWEEN_STILLS
                # print("frame_delta: " + str(frame_delta))

                if j == 0 or j % int(frame_delta) == 0:
                    # print("Taking snap at frame {} and estimated second {}".format(j, j / fps))
                    filepath = imagesPath + "\\" + videoID + str(count) + ".jpg"

                    ret = cv.imwrite(filepath, frame)
                    if not ret:
                        print("Failed to write image.  ID: {}  Instant: {}".format(videoID, i))
                    else:
                        count += 1 
        cap.release()


    def validIntervals(self, intervals):
        previous_later = 0.0

        for i in intervals:
            if i.start < previous_later:
                return False
            if i.start >= i.end:
                return False

            previous_later = i.end

        return True

    def get_video(self, id):
        url= "https://www.youtube.com/watch?v=" + id
        vid = pafy.new(url)
        best = vid.getbest(preftype="mp4")
        best.download(filepath = self.video_directory + "\\" + id + ".mp4" ,quiet = True) 



# def cut_segments(title,segments):
#     for segment in segments:
#         if  '-' not in segment:
#             print("not a time segment")
#         else:
#             principio,fin = segment.split("-")
#             principio = principio.replace(" ","")
#             principio = get_secs(principio)
#             fin = fin.replace(" ","")
#             fin = get_secs(fin)
#             ffmpeg_extract_subclip(title+".mp4", principio,fin, targetname=title+" "+str(principio)+"-"+str(fin)+".mp4")
            
# def obtain_data(reader):
#     for row in reader:
#         video = videos
#         video.vidID = row[0]
#         row.remove(video.vidID)
#         video.times = row
#         listvids.append(video)
#         try:
#             get_video(video.vidID)
#         except:
#             newReader.append(row)
#             print("Numero de Videos Fallidos: ", len(newReader))
#         cut_segments(video.vidID,video.times)
#         print("Operacion completada en:"+ str(time.time() - timer))
#         if len(newReader) > 0:
#             obtain_data(newReader)
#             print("reintentando")