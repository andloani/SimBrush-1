# ----------- Imports --------------------------------------------------------------------------------
import time, string, logging, getopt, sys, os, time
from xml.dom.minidom import *

from reportlab.rl_config import defaultPageSize
PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle, NextPageTemplate
from  reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate, _doNothing
from  reportlab.platypus.tableofcontents import TableOfContents
from  reportlab.platypus.frames import Frame

from messaging.sms import SmsDeliver

# ----------- Globals -------------------------------------------------------------------------------
filename = ""
outputFile = "report.pdf"
reportVersion = "1.0"

# Array to store document data
Story=[]

# ----------- Tables styles ------------------------------------------------------------------------

tableStyleWithHeader = TableStyle([
	('GRID', (0,0), (-1,-1), 1, colors.black),
	('TEXTCOLOR',(0,0),(1,0),colors.black),
	('BACKGROUND',(0,0),(1,0),colors.lightgrey),
	('TEXTCOLOR',(0,1),(1,-1),colors.black),
	('SIZE', (0,0), (-1,-1), 8),
	('TOPPADDING', (0,0), (-1,-1), 0),
	('BOTTOMPADDING', (0,0), (-1,-1), 0),
	('LEFTPADDING', (0,0), (-1,-1), 5),
	('RIGHTPADDING', (0,0), (-1,-1), 5),
])

tableStyleStandard = TableStyle([
	('GRID', (0,0), (-1,-1), 1, colors.black),
	('TEXTCOLOR',(0,1),(1,-1),colors.black),
	('SIZE', (0,0), (-1,-1), 10),
	('TOPPADDING', (0,0), (-1,-1), 2),
	('BOTTOMPADDING', (0,0), (-1,-1), 2),
	('LEFTPADDING', (0,0), (-1,-1), 5),
	('RIGHTPADDING', (0,0), (-1,-1), 5),
])

tableStyleSingleRow = TableStyle([
	('BOX', (0,0), (-1,-1), 1, colors.black),
	('TEXTCOLOR',(0,1),(1,-1),colors.black),
	('SIZE', (0,0), (-1,-1), 10),
	('TOPPADDING', (0,0), (-1,-1), 1),
	('BOTTOMPADDING', (0,0), (-1,-1), 1),
	('LEFTPADDING', (0,0), (-1,-1), 5),
	('RIGHTPADDING', (0,0), (-1,-1), 5),
])

# ----------- Logger --------------------------------------------------------------------------------

# Logger
log = logging.getLogger('Report Builder')
log.setLevel(logging.WARNING)
#create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
#create formatter
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
#add formatter to ch
ch.setFormatter(formatter)
#add ch to logger
log.addHandler(ch)

# ----------- Command Line Parameters ---------------------------------------------------------------
def usage():
	print("")
	print("SimBrush data reporter (ver. %s)\n"%reportVersion)
	print("Usage: report.py -f inputfilename")
	print("Other options:")
	print("-h  \t\t\tthis help")
	print("-v  \t\t\tverbose")
	print("-o outputfilename \t(default: report.pdf)")
	print("")

try:
	opts, args = getopt.getopt(sys.argv[1:], "hf:o:v")
except getopt.GetoptError:
	usage()
	sys.exit(0)

for o,a in opts:
	if o == "-v":
		log.setLevel(logging.INFO)
		ch.setLevel(logging.INFO)
	elif o == "-h":
		usage()
		system.exit(0)
	elif o == "-f":
		filename = a
	elif o == "-o":
		outputFile = a

if (len(filename) == 0):
	usage()
	print("You need to provide an input file name.\n")
	sys.exit(0)
	
if (os.path.isfile(filename) == 0):
	usage()
	print("File \"filename\" does not exist!\n")
	sys.exit(0)

# ----------- Document template ---------------------------------------------------------------------
class MyDocTemplate(BaseDocTemplate):
	def __init__(self, filename, **kw):
		self.allowSplitting = 0
		apply(BaseDocTemplate.__init__, (self, filename), kw)

	def afterFlowable(self, flowable):
		"Registers TOC entries."
		if flowable.__class__.__name__ == 'Paragraph':
			text = flowable.getPlainText()
			style = flowable.style.name
			if style == 'Heading1':
				self.notify('TOCEntry', (0, text, self.page))
			if style == 'Heading2':
				self.notify('TOCEntry', (1, text, self.page))
			if style == 'Heading3':
				self.notify('TOCEntry', (2, text, self.page))

	def multiBuild(self,flowables,onFirstPage=_doNothing, onLaterPages=_doNothing): 
		self._calc() #in case we changed margins sizes etc 
		frameFirst = Frame(2*cm, 2*cm, 17*cm, 23*cm, id='F1')
		frameLater = Frame(2.5*cm, 2*cm, 16*cm, 24.5*cm, id='F2')
		
		self.addPageTemplates([
			PageTemplate (id='First',frames=frameFirst, onPage=onFirstPage, pagesize=self.pagesize), 
			PageTemplate(id='Later',frames=frameLater, onPage=onLaterPages, pagesize=self.pagesize)
		]) 
		
		BaseDocTemplate.multiBuild(self,flowables) 
		
centered = ParagraphStyle(name = 'centered',
    fontSize = 30,
    leading = 16,
    alignment = 1,
    spaceAfter = 20)

h1 = ParagraphStyle(
    name = 'Heading1',
    fontSize = 12,
    leading = 16)

h2 = ParagraphStyle(name = 'Heading2',
    fontSize = 10,
    leading = 14)

h3 = ParagraphStyle(name = 'Heading3',
    fontSize = 10,
    leading = 14)
   
# ----------- Cover ----------------------------------------------------------------------------

Title = "SimBrush %s report"%reportVersion
pageinfo = "SimBrush Report"

# Standard elements drawn in the first page
def myFirstPage(canvas, doc):
	canvas.saveState()
	canvas.setFont('Times-Bold',16)
	canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-2.5*cm, Title)
	
	canvas.line(0 + PAGE_WIDTH/3,PAGE_HEIGHT - 3*cm, PAGE_WIDTH * 2 / 3, PAGE_HEIGHT - 3*cm)
	
	canvas.setFont('Times-Roman',9)
	canvas.drawString(inch, 0.75 * inch,"First Page / %s" % pageinfo)
	canvas.restoreState()

# Standard elements drawn in following pages
def myLaterPages(canvas, doc):
	canvas.saveState()
	
	canvas.setFont('Times-Bold',10)
	canvas.drawString(inch, PAGE_HEIGHT - inch, Title)
	
	canvas.line(inch, PAGE_HEIGHT - 3*cm, PAGE_WIDTH - inch, PAGE_HEIGHT - 3*cm)
	
	canvas.setFont('Times-Roman', 9)
	canvas.drawString(10*cm, PAGE_HEIGHT - inch,"Page %d" % (doc.page))
	canvas.restoreState()

# ----------- Print functions ----------------------------------------------------------------------
# Prints the header data table from the "header" node
def printHeader(headerNode):
	ptext = "Header data:"
	Story.append(Paragraph("<font size=10>%s</font>"%ptext, styles["Normal"]))
	
	Story.append(Spacer(1, 12))
	
	headerData = [['Field name','Field data']]
	for element in headerNode.childNodes:
		if (element.nodeType == element.TEXT_NODE): continue
		headerData.append([Paragraph("<font size=8>%s</font>"%element.localName, styles["Normal"]), Paragraph("<font size=8>%s</font>"%element.firstChild.toxml(), styles["Normal"])])
	
	t=Table(headerData, colWidths=[100, 350])
	t.setStyle(tableStyleWithHeader)
	Story.append(t)

	Story.append(PageBreak())

# Print file data (along with header data if found)
def printFile(file, toplevel = ""):
	
	# print file name as page title
	if (toplevel == ""):
		ptext = "%s"%(file.localName)
	else:
		ptext = "%s / %s"%(toplevel, file.localName)
	Story.append(Paragraph("<font size=14>File: %s</font>"%ptext, styles["Normal"]))
	
	Story.append(Spacer(1, 12))
	
	# print file description (attribute "description")
	description = file.attributes['description'].value
	ptext = "%s"%description
	Story.append(Paragraph("<font size=10>%s</font>"%ptext, styles["Normal"]))
	
	Story.append(Spacer(1, 12))
	
	# look for unknown elements contained in EF files 
	# not "header" nor "content"
	for element in file.childNodes:
		if (element.localName == "header"): continue;
		if (element.localName == "content"): continue;
		if (element.nodeType == element.TEXT_NODE): continue
		
		log.warning("Element of not standard type \"%s\" in \"%s\". Ignored."%(element.localName, file.localName))
	
	# print header data (if available)
	header = file.getElementsByTagName('header')
	if (len(header) > 0):
		ptext = "Header data:"
		Story.append(Paragraph("<font size=10>%s</font>"%ptext, styles["Normal"]))
		
		Story.append(Spacer(1, 12))
		
		headerData = [['Field name','Field data']]
		for element in header[0].childNodes:
			if (element.nodeType == element.TEXT_NODE): continue
			headerData.append([element.localName, element.firstChild.toxml()])
		
		t=Table(headerData, colWidths=[100, 350])
		t.setStyle(tableStyleWithHeader)
                       
		Story.append(t)
	else:
		Story.append(Paragraph("<font size=10>Header data not available</font>", styles["Normal"]))
		log.info("Header data not found for EF file %s"%file.localName)
	
	Story.append(Spacer(1, 12))
		
	# File content
	
	ptext = "File content:"
	Story.append(Paragraph("<font size=10>%s</font>"%ptext, styles["Normal"]))
	Story.append(Spacer(1, 12))
	
	contents = file.getElementsByTagName('content')
	
	if (len(contents) < 1):
		Story.append(Paragraph("<font size=10>No file content</font>", styles["Normal"]))
		log.info("No content for EF file %s"%file.localName)
		
	index = 0
	emptyCount = 0
	for content in contents:
	
		#content nodes with just text		
		if (len(content.childNodes) == 1):
		
			elementData = []
			if (content.firstChild.toxml() == "Empty"): 
				emptyCount += 1
				continue
			
			# SMS Data file
				
			if (file.localName == "SMS"):
				elementData = [['Field name','Field data']]
				
				def addLine(one, two):
					elementData.append([
						Paragraph("<font size=8>%s</font>"%one, styles["Normal"]),
						Paragraph("<font size=8>%s</font>"%two, styles["Normal"])
						])
				
				smsData = string.strip(content.firstChild.toxml())
				smsData = smsData[2:]
				
				try:
					sms = SmsDeliver(smsData)
				except:
				
					# if unable to decode SMS
					log.info('Unable to decode SMS structure (probably empty record)')
					elementData.append([
						Paragraph("<font size=8>ERR</font>", styles["Normal"]),
						Paragraph("<font size=8>Unable to decode, probably empty record</font>", styles["Normal"])
					])
					
					length = 70
					smsDataRows = [smsData[i:i+length] for i in range(0, len(smsData), length)]
					
					for row in smsDataRows:
						elementData.append([
							Paragraph("", styles["Normal"]),
							Paragraph("<font size=8>%s</font>"%row, styles["Normal"])
						])	
							
					t=Table(elementData, colWidths=[50, 400])
					t.setStyle(tableStyleWithHeader)
					Story.append(t)
					
					Story.append(Spacer(1, 2))

					continue
				
				# if sms data decoded correctly
				addLine('Csca', sms.csca)
				addLine('Number', sms.number)
				addLine('Date', sms.date)
				addLine('Text', sms.text)
				addLine("Meta", "SR: %s, FMT: %s, PID: %s, Type: %s, DCS: %s"%(sms.sr, sms.fmt, sms.pid, sms.type, sms.dcs))
				
				t=Table(elementData, colWidths=[50, 400])
				t.setStyle(tableStyleWithHeader)
				Story.append(t)
				
				Story.append(Spacer(1, 2))
				
			# any other type of file
			else:	
					
				# string split by '###'
				string_rows = string.split(content.firstChild.toxml(), '###')
				
				# Insert string rows in table rows (with index in the first row)
				firstLine = 1
				for string_row in string_rows:
					if (len(string_row.strip()) == 0): continue
					indexData = ''
					if firstLine == 1:
						indexData = index
					firstLine = 0
					ptext = string_row
					elementData.append([
						Paragraph("<font size=8>%s</font>"%indexData, styles["Normal"]), 
						Paragraph("<font size=8>%s</font>"%ptext, styles["Normal"])
					]);
					
				if (len(elementData) > 0):
					t=Table(elementData, colWidths=[20, 430])
					t.setStyle(tableStyleSingleRow)
			                       
					Story.append(t)
					Story.append(Spacer(1, 2))
			
		#content nodes with an underlying structure
		else:
			elementData = [['Field name','Field data']]
			elements = content.childNodes
			for element in elements:
				if (element.nodeType == element.TEXT_NODE): continue
				
				elementData.append([Paragraph("<font size=8>%s</font>"%element.localName, styles["Normal"]), Paragraph("<font size=8>%s</font>"%element.toxml(), styles["Normal"])])
		
			t=Table(elementData, colWidths=[100, 350])
			t.setStyle(tableStyleWithHeader)
	                       
			Story.append(t)
			Story.append(Spacer(1, 12))
	
		index += 1
	
	if (emptyCount > 0):
		Story.append(Spacer(1, 12))
		Story.append(Paragraph("<font size=10>The file also contains %i empty fields.</font>"%emptyCount, styles["Normal"]))
	
	Story.append(PageBreak())

# ----------- Various functions ----------------------------------------------------------------
# Returns the number of child nodes for the specified node
# (not counting text nodes)
def checkNumberOfChildNodes(node):
	count = 0
	for element in node.childNodes:
		if (element.nodeType == element.TEXT_NODE): continue;
		count += 1
	return count

# Prints error if passed node contains more than one child
def checkSingleChild(node):
	number = checkNumberOfChildNodes(node)
	if (number != 1):
		log.warning("Top level EF file containing first child \"%s\" has %i child nodes. Ignoring ones after first."%(node.childNodes[1].localName, number))	

# ----------- Default style --------------------------------------------------------------------
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

# ----------- First Page --------------------------------------------------------------------
coverData = [
	['Input XML file', filename],
	['Creation date of input file', time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(os.path.getmtime(filename)))],
	['Creation date of this report', time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())],
]

t=Table(coverData, colWidths=[150, 300])
t.setStyle(tableStyleStandard)                   
Story.append(t)

Story.append(NextPageTemplate('Later'))

Story.append(PageBreak())

# ----------- Table of Contents ----------------------------------------------------------------
Story.append(Paragraph("<font size=12>Table of Contents</font>", styles["Normal"]))
Story.append(Spacer(1, 6))

toc = TableOfContents()
toc.dotsMinLevel = 0
toc.levelStyles = [
    ParagraphStyle(
    	fontName='Times-Bold', 
    	fontSize=12, 
    	name='TOCHeading1', 
    	leftIndent=20, 
    	firstLineIndent=-20, 
    	spaceBefore=5, 
    	leading=6
    ),
    ParagraphStyle(
    	fontSize=10, 
    	name='TOCHeading2', 
    	leftIndent=40, 
    	firstLineIndent=-20, 
    	spaceBefore=2, 
    	leading=6
    ),
    ParagraphStyle(
    	fontSize=10, 
    	name='TOCHeading3', 
    	leftIndent=60, 
    	firstLineIndent=-20, 
    	spaceBefore=2, 
    	leading=6
    ),
]
Story.append(toc)

Story.append(PageBreak())

# ----------- Acquire the XML tree from the input file ----------------------------------------------
print("\nAnalyzing \"%s\"..."%filename)
manifest = parse(filename)

# Root elements
OPT_node = manifest.getElementsByTagName("opt")[0]
MF_node = OPT_node.getElementsByTagName("MF")[0]

# Analyze XML tree

# search for header
headerfound = 0
for toplevel in MF_node.childNodes:
	if (toplevel.localName != "header"): continue;
	Story.append(Paragraph("Main header data", h1))
	printHeader(toplevel)
	headerfound = headerfound + 1

if (headerfound == 0):
	log.info("Not found header data for top level")
if (headerfound > 1):
	log.warning("%i header elements found in toplevel"%(headerfound))

# other elements
for toplevel in MF_node.childNodes:
	if (toplevel.nodeType == toplevel.TEXT_NODE): continue;
	if (toplevel.localName == "header"): continue;
	
	toplevelname = toplevel.localName
	
	# files directly in top level (ICCID, ELP)
	if (toplevel.localName == "EF"):
		checkSingleChild(toplevel)
		Story.append(Paragraph(toplevel.childNodes[1].localName, h1))
		printFile(toplevel.childNodes[1], "")
	
	# files in second level (DF_7F10, DF_7F20)
	else:
		Story.append(Paragraph(toplevelname, h1))
		
		# look for header
		headerfound = 0
		for element in toplevel.childNodes:
			if (element.localName != "header"): continue;
			printHeader(element)
			headerfound = 1
		if (headerfound == 0):
			log.info("Header data not found for %s"%toplevelname)
		
		# print non-header elements
		for element in toplevel.childNodes:
			
			if (element.nodeType == element.TEXT_NODE): continue;
			if (element.localName == "header"): continue;
				
			if (element.localName == "EF"):
				checkSingleChild(element)
				firstChild = element.childNodes[1]
				Story.append(Paragraph(firstChild.localName, h2))
				printFile(firstChild, toplevelname)
			else:
				subfiles = element.childNodes
				sublevelname = element.localName
				
				Story.append(Paragraph(sublevelname, h2))
				
				for filecont in subfiles:
					if (filecont.nodeType == filecont.TEXT_NODE): continue;
					if (filecont.localName == "EF"):
						checkSingleChild(filecont)
						file = filecont.childNodes[1]
						if(file.nodeType == file.TEXT_NODE): continue;
						Story.append(Paragraph(file.localName, h3))
						printFile(file, toplevelname + " / " + sublevelname);
					else:
						log.warning("Third level element \"%s\" not EF file. Ignoring."%filecont.localName)


print("Building output file \"%s\"..."%outputFile)
doc = MyDocTemplate(outputFile)
#doc.multiBuild(Story)
doc.multiBuild(Story, onFirstPage=myFirstPage, onLaterPages=myLaterPages)

print("Output completed.\n")