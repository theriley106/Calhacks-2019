from flask import Flask, render_template, jsonify, request
from flask_sockets import Sockets
import datetime
import time
import json
import textstat
import requests
import traceback
from pdf2image import convert_from_path
from wand.color import Color
from wand.image import Image
from PIL import ImageFont, ImageDraw, ImageEnhance
import PIL
import pdfParse
import email_client as email_form
import random
from time import gmtime, strftime
import threading

import os
import sys
sys.path.insert(0,'text-summarization/')

from text_sum import TextSummarizer

app = Flask(__name__)

sockets = Sockets(app)

DB = json.load(open("documentDataDB.json"))

RESPONSES = [None]

LOGS = [None]

TOTAL = [1]
FOUND = [False]


def add_log(stringVal):
	if FOUND[-1] == False:
		timeVal = strftime("%H:%M:%S", gmtime())
		LOGS.append("{} | {}".format(timeVal, stringVal))
	print("ADDED LOG")

@sockets.route('/logs')
def logs(webSocket):
	prev = "AYYY"
	while True:
		try:
			if prev != LOGS[-1]:
				if LOGS[-1] != None:
					webSocket.send(str(LOGS[-1]))
				else:
					webSocket.send("-")
				prev = LOGS[-1]
		except Exception as exp:
			print traceback.print_exc()
			print("Exception in get logs" + str(exp))
		time.sleep(.1)

def send_text_to_api():
	add_log("concatenating pdf pages to a single image | eta: 10 seconds")
	text = convert_pdf_to_png("static/tesla.pdf")
	ts = TextSummarizer({"data": text})
	email_form.send_document_for_signing(ts.get_summary())
	return ts.get_summary()

def get_progress_bars():
	return ''

@app.route("/update")
def updated():
	# FOUND[-1] = True
	print("updated")
	#LOGS.append(get_progress_bars())
	#time.sleep(.3)
	print("ADDED PROGRESS BARS")
	with open('documentDataDB.json', 'w') as outfile:
		json.dump(DB, outfile, indent=4)
	add_log("confirmed the document has been read")
	if len(TOTAL) > 0:
		TOTAL.pop()
		threading.Thread(target=send_text_to_api).start()
	return "AYY"

@sockets.route('/getUpdatedFromDocusign')
def echo_socket_docusign(ws):
	prev = "AYYY"
	while True:
		try:
			if prev != RESPONSES[-1]:
				updated()
				ws.send(str(RESPONSES[-1]))
				prev = RESPONSES[-1]
		except Exception as exp:
			print traceback.print_exc()
			print("Exception in get updated from docusign" + str(exp))
		time.sleep(.1)

def convert_pdf_to_png(filenameVal):
	pdf = Image(filename=filenameVal, resolution=200)

	pages = len(pdf.sequence)

	image = Image(
		width=pdf.width,
		height=pdf.height * pages
	)

	for i in xrange(pages):
		image.composite(
			pdf.sequence[i],
			top=pdf.height * i,
			left=0
		)
	image.background_color = Color("white")
	image.alpha_channel = 'remove'
	image.save(filename="out.png")
	return remove_points_from_image(filenameVal)

def remove_points_from_image(filenameVal):
	add_log("removing comprehended parts from image | eta: 10 seconds")
	source_img = PIL.Image.open("out.png").convert("RGBA")
	width, height = source_img.size
	draw = ImageDraw.Draw(source_img)
	for val in DB[filenameVal.partition("/")[2]].keys():
		y = float(height * float(val))
		# print(y)
		draw.rectangle(((0, y), (width, y+40)), fill="white")
	# draw.text((20, 70), "something123", font=ImageFont.truetype("font_path123"))
	source_img.save("newFile.png", "png")
	add_log("converting remaining image to text via OCR")
	return pdfParse.Get_text_from_image("newFile.png")

def extract_unused_sentences(fileName):
	pages = convert_from_path('pdf_file', 500)
	for page in pages:
		convert_pdf_to_png("static/tesla.pdf").save('out.png', 'png')
	DB[fileName].values()
	return 

@sockets.route('/chrisDocusignEndpointDotExe')
def echo_socket(ws):
	prev = "NONE"
	while True:
		if not ws.closed:
			message = ws.receive()
			try:
				# print(message)\
				position, fileName = message.split(",")
				if position == "-1":

					if position != prev:
						if prev != "NONE":
							updated()
						else:
							add_log("User has started reading the beginning of the document")
				elif position == "9999999":
					if position != prev:
						add_log("User has hit the end of the document")
				else:
					if position != prev:
						add_log("User started reading at {}px".format(int(float(position) * 2054)))
					smallFilename = fileName.replace("/static/", "")
					if smallFilename not in DB:
						DB[smallFilename] = {}
					if position not in DB[smallFilename]:
						DB[smallFilename][position] = 0
					DB[smallFilename][position] += 1
					ws.send(str(datetime.datetime.now()))
				prev = position
			except Exception as exp:
				print("ERROR" + str(exp))
			print message
			
			# print(DB)
		time.sleep(.1)

@app.route("/pdfAnalyticsGenerate/<documentName>")
def doAnalytics(documentName):
	DB[documentName] = {}
	return render_template('pdfThingGet.html')

@app.route("/pdfAnalyticsView/<documentName>")
def doAnalyticsView(documentName):
	return render_template('pdfThingView.html')
	with open('documentDataDB.json', 'w') as outfile:
		json.dump(DB, outfile, indent=4)
	return jsonify(DB.get(documentName, []))
	# return render_template('pdfThingView.html', MY_PDF_AYYO="/static/{}".format(documentName))

@app.route('/add', methods=['GET'])
def add():
	if random.randint(1,4) == 3:
		LOGS.append(json.dumps({"type": "sentiment", "amount": str(random.randint(50, 100))}))
	else:
		LOGS.append("AYYYYY THIS WORKS" + str(random.randint(1,10000)))
	return ""

@app.route("/getDataOnDocument/<documentName>")
def getData(documentName):
	points = []
	width = float(request.args.get("width"))
	height = float(request.args.get("height"))
	# raw_input(str(width) + str(height))
	for key, val in DB.get(documentName, {}).iteritems():
		try:
			# print(int(val/5))

			val = float(val)
			if height == 0:
				height = 100
			y = height * (float(key))
			if y < 100:
				y += 100
			for i in range(int(val / 5)):
				x = 40
				while x < width-20:
					points.append({"x": int(x), "y": int(y), "value": int(val/5)})
					x += 10
				y += 10
		except Exception as exp:
			print(exp)
			pass
	return jsonify({"data": points})

@app.route('/echo_test', methods=['GET'])
def echo_test():
	return render_template('display.html')

@app.route('/admin', methods=['GET'])
def admin():
	return render_template('admin.html')

@app.route('/index', methods=['GET'])
def index():
	return render_template('index.html')

@app.route('/textAnalytics', methods=['GET', 'POST'])
def text_analytics():
	return jsonify({"result": textstat.flesch_reading_ease(request.form.get("text"))})
	# return render_template('index.html')

@app.route('/summarization', methods=['POST'])
def run_summarization():
	add_log("summarizing text using Microsoft Azure | eta: 30 seconds")
	data = request.data
	ts = text_sum.TextSummarizer(data)
	result = ts.get_summary()
	add_log("sending email with generated document using Docusign esigning api")
	send_email(summary)
	return jsonify({"result":["line"]})


def send_email(summary):
	email_form.send_email_for_signing(summary)

if __name__ == '__main__':
	app.run()
	# Start with gunicorn -k flask_sockets.worker app:app
