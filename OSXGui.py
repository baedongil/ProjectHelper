import subprocess
import fileinput
import sys
import time
import os
from xml.etree.ElementTree import parse
import urllib        
from bs4 import BeautifulSoup
import codecs
import threading

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.clock import Clock

_ipaName = ''
_svnVersionNum = ''
_svnVersion = ''
_buildCount = 0
_oneshot = False

class CommandTread(threading.Thread):
    cmd = ''
    buildLog = False
    def __init__(self,parent=None):
        self.parent = parent
        threading.Thread.__init__(self)
    
    def setCommand(self,command,log):
        self.cmd = command
        self.buildLog = log
        
    def run(self):
        process = subprocess.Popen(self.cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        while True:
            nextline = process.stdout.readline()
            if nextline == '' and process.poll() != None:
                if self.buildLog:
                    self.parent.buildEnd()
                else:
                    self.parent.makeIpaEnd()
                break
            if self.buildLog:
                self.parent.progressLog(nextline)
            else:
                self.parent.log(nextline)

class OSXGuiWidget(GridLayout):
    baseDirPath = StringProperty()
    dstIpaPath = StringProperty()
    baseSmbPath = StringProperty()
    baseHtmlPath = StringProperty()
    
    consoleLabel = ObjectProperty()
    baseInputText = ObjectProperty()
    ipaInputText = ObjectProperty()
    dstPathInputText = ObjectProperty()
    htmlPathInputText = ObjectProperty()
    majorInputText = ObjectProperty()
    versionTitleInputText = ObjectProperty()
    
    pb_progressbar = ObjectProperty()
    
    baseDirPath = os.path.dirname(os.path.abspath(__file__)) + '/../../../POCloud'
    baseSmbPath = '/Volumes/iOS-Dist/download/POL'
    baseHtmlPath = '/Volumes/iOS-Dist/iOS'
    #baseSmbPath = '/Volumes/mac_share/kivy'
    #baseHtmlPath = '/Volumes/mac_share/kivy/test_mac_share.html'
    
    def __init__(self, **kwargs):
        super(OSXGuiWidget, self).__init__(**kwargs)
        Clock.schedule_once(self.prepare, 0)

    def prepare(self, *args):
        self.baseInputText = self.ids.path_textinput.__self__
        self.ipaInputText = self.ids.ipa_textinput.__self__
        self.consoleLabel = self.ids.console_label.__self__
        self.pb_progressbar = self.ids.pb_progressbar.__self__
        self.dstPathInputText = self.ids.dstpath_textinput.__self__
        self.htmlPathInputText = self.ids.dsthtmlpath_textinput.__self__
        self.majorInputText = self.ids.major_textinput.__self__
        self.versionTitleInputText = self.ids.htmlTitle_textinput.__self__
        
    def do_onText(self):
        global _ipaName
        _ipaName = self.ipaInputText.text

    def do_svnUpdate(self):
        global _svnVersionNum
        global _svnVersion
        svnCommand = "svn up " + self.baseInputText.text
        result = subprocess.check_output(svnCommand, shell=True)
        self.log(result)
        offset = result.find('At revision ')
        if  offset > 0 :
            _svnVersion = result[offset+12:]
            _svnVersion = _svnVersion[:_svnVersion.find('.')]
            _svnVersionNum = _svnVersion
            _svnVersion = _svnVersion[:3] +'.' +_svnVersion[3:]
        """
        stepLogging('UDefine Version Update...')
        
        """
    def do_modifyUdefine(self):
        if len(self.majorInputText.text) == 0 :
            self.log('input major version')
            return 
        global _ipaName
        if len(_svnVersion) == 0 and len(_svnVersionNum) == 0 :
            self.log('need for svn update...')
            return 
        print self.baseInputText.text +'/office5/UFrame/UDefine.h'
        file = open(self.baseInputText.text +'/office5/UFrame/UDefine.h', 'r+')
        lines = file.xreadlines()
        for line in lines:
            ret = self.modifyVersion(file,line,_svnVersion)
            if ret != None and len(ret) > 0 :
                self.log(ret)
        _ipaName = 'POL'+ self.majorInputText.text+ time.strftime('_%y%m%d_%H%M_') + _svnVersionNum +'.ipa'
        self.ipaInputText.text = _ipaName
    
    def getVersion(self):
        global _svnVersion
        global _svnVersionNum
        file = open(self.baseInputText.text +'/office5/UFrame/UDefine.h', 'r+')
        lines = file.xreadlines()
        for line in lines:
            if line.find('_UAppBuildVersion') > 0 :
                offsetS = line.rfind('.')-3
                offsetE = line.rfind('-IU') 
                _svnVersion = line[offsetS:offsetE]
                _svnVersionNum = _svnVersion.replace('.', '')
                self.log('svn version ' + _svnVersion +' : '+ _svnVersionNum + '\n')
        
    def do_xcodebuild(self):
        global _buildCount
        _buildCount = 0
        xcodeBuildCommand = 'xcodebuild -project '+ self.baseInputText.text + '/office5.xcodeproj -scheme PolarisOffice -destination generic/platform=iOS archive DSTROOT="build"'
        commandThread = CommandTread(self)
        commandThread.setCommand(xcodeBuildCommand, True)
        commandThread.start()
    
    def do_xcodeclean(self):
        xcodeBuildCommand = 'xcodebuild -project '+ self.baseInputText.text + '/office5.xcodeproj -scheme PolarisOffice -destination generic/platform=iOS clean'
        commandThread = CommandTread(self)
        commandThread.setCommand(xcodeBuildCommand, True)
        commandThread.start()
        
    def do_makeipa(self):
        global _ipaName
        if len(self.majorInputText.text) == 0 :
            self.log('input major version')
            return
        if len(self.ipaInputText.text) == 0:
            self.getVersion()
            _ipaName = 'POL'+ self.majorInputText.text+ time.strftime('_%y%m%d_%H%M_') + _svnVersionNum +'.ipa'
            self.ipaInputText.text = _ipaName
        productPath = os.path.dirname(os.path.abspath(__file__)) + '/../../../Product/'
        try:
            os.stat(productPath)
        except:
            os.mkdir(productPath)     
        xcurnCommand = 'xcrun -sdk iphoneos PackageApplication -v '+ self.baseInputText.text + '/build/Applications/PolarisOffice.app -o ' + productPath + self.ipaInputText.text
        print xcurnCommand
        commandThread = CommandTread(self)
        commandThread.setCommand(xcurnCommand, False)
        commandThread.start()
    
    def do_copySMB(self):
        productPath = os.path.dirname(os.path.abspath(__file__)) + '/../../../Product/'
        if len(self.ipaInputText.text) == 0:
            self.getVersion()
            self.getIpaName(productPath)
        if len(self.ipaInputText.text) > 1:
            self.modifyHtml(self.ipaInputText.text)
            self.modifyPList(self.ipaInputText.text, _svnVersionNum)
            self.copySMB()
        else:
            self.log('Error !! You must make ipa file...')
    
    def do_oneShot(self):
        global _oneshot
        _oneshot = True
        self.do_svnUpdate()
        self.do_modifyUdefine()
        self.do_xcodebuild()
        
    def buildEnd(self):
        self.log('\nbuild end!!')
        global _oneshot
        if _oneshot:
            self.do_makeipa() 
    
    def makeIpaEnd(self):
        global _oneshot
        self.log('\nipa make end!!')
        if _oneshot:
            self.do_copySMB()
    
    def getIpaName(self,path):
        global _ipaName
        for fname in os.listdir(path):
            full_dir = os.path.join(path, fname)
            if os.path.isdir(full_dir):
                print 'dir : ' + fname 
            else :
                print fname
                if full_dir.find('.ipa') > 0 :
                    _ipaName = fname
                    self.ipaInputText.text = _ipaName
        
        
    def modifyVersion(self,file,line,version):
        if line.find('_UAppBuildVersion') > 0 :
            replaceS = line.rfind('.')-3
            replaceE = line.rfind('-IU') 
            replaceLine = line[:replaceS] + version + line[replaceE:]
            self.replaceAll(self.baseInputText.text + '/office5/UFrame/UDefine.h', line, replaceLine)
            return line + '->' + replaceLine
        if line.find('_UAppBuildDate') > 0 :
            replaceS = line.find('"')+1
            replaceE = line.rfind('"') 
            replaceDate = time.strftime('%y%m%d:%H%M')
            replaceLine = line[:replaceS] + replaceDate + line[replaceE:]
            self.replaceAll(self.baseInputText.text + '/office5/UFrame/UDefine.h', line, replaceLine)
            return line + '->' + replaceLine
    
    def replaceAll(self,file,searchExp,replaceExp):
        for line in fileinput.input(file, inplace=1):
            if searchExp in line:
                line = line.replace(searchExp,replaceExp)
            sys.stdout.write(line)
    
    def stripLine(self,str,num):
        str = str[str[:str.rfind('\n')-1].rfind('\n')+1:]
        return str
    
    def progressLog(self,str):
        global _buildCount
        _buildCount+=1
        if _buildCount < self.pb_progressbar.max:
            self.pb_progressbar.value = _buildCount
        self.log(str)
        
    def log(self,str):
        if self.consoleLabel.text.count('\n') + str.count('\n') > 16:
            self.consoleLabel.text = self.stripLine(self.consoleLabel.text,1) + str
        else:
            self.consoleLabel.text = self.consoleLabel.text + str
    
    def copySMB(self):
        global _ipaName
        if len(self.majorInputText.text) == 0 :
            self.log('Error: majorVersion Get Fail...')
            return
        productPath = os.path.dirname(os.path.abspath(__file__)) + '/../../../Product/'
        cpIpaCommand = 'cp '+ productPath + _ipaName + ' ' + self.dstPathInputText.text + '/' + self.majorInputText.text
        try:
            subprocess.check_call(cpIpaCommand, shell=True)
        except:
            self.log('\nError:\n'+ cpIpaCommand)
        cpPlistCommand = 'cp ./Base.plist' + ' ' + self.dstPathInputText.text + '/' + self.majorInputText.text + '/' + _ipaName[:_ipaName.rfind('.ipa')] + '.plist'
        try:
            subprocess.check_call(cpPlistCommand, shell=True)
        except:
            self.log('\nError:\n'+ cpPlistCommand)
        cpHtmlCommand = 'cp ./output.html' + ' ' + self.htmlPathInputText.text
        try:
            subprocess.check_call(cpHtmlCommand, shell=True)
        except:
            self.log('\nError:\n'+ cpHtmlCommand)
        self.log('End')

    def modifyPList(self,ipaName,svnVersionNum):
        if len(self.majorInputText.text) == 0 :
            self.log('input major version')
            return 
        downPathPrefix = 'https://apps.infraware.net:9999/download/POL'
        file = open('./Base.plist', 'r+')
        lines = file.readlines()
        for i in range(0,len(lines)):
            line = lines[i]
            if line.find(downPathPrefix) > 0 :
                replaceS = line.find(downPathPrefix)+len(downPathPrefix)
                replaceE = line.rfind('</string>')
                replaceLine = line[:replaceS] + '/' + self.majorInputText.text + '/' + ipaName + line[replaceE:]
                self.replaceAll('./Base.plist', line, replaceLine)
                self.log(line + 'change    ----- > ' + replaceLine)
            if line.find('bundle-version') > 0 :
                majorVersion = self.majorInputText.text
                nextLine = lines[i+1]
                replaceS = nextLine.find('<string>')+8
                replaceE = nextLine.rfind('</string>')
                replaceLine = nextLine[:replaceS] + majorVersion[0]+'.'+majorVersion[1]+'.'+majorVersion[2]  + nextLine[replaceE:]
                self.replaceAll('./Base.plist', nextLine, replaceLine)
                self.log(nextLine + 'change    ----- > ' + replaceLine)
            if line.find('<key>title</key>') > 0 :
                nextLine = lines[i+1]
                replaceS = nextLine.find('<string>')+8
                replaceE = nextLine.rfind('</string>')
                replaceLine = nextLine[:replaceS] + 'build ' + svnVersionNum + nextLine[replaceE:]
                self.replaceAll('./Base.plist', nextLine, replaceLine)
                self.log(nextLine + 'change    ----- > ' + replaceLine)
            
    def modifyHtml(self,ipaName):
        if len(self.majorInputText.text) == 0 :
            self.log('input major version')
            return 
        soup = None
        try:
            urlString = 'https://apps.infraware.net:9999/iOS/'
            data = urllib.urlopen(urlString)
            soup = BeautifulSoup(data.read(),from_encoding="euc-kr")    
        except:
            htmlDoc = codecs.open('Base.html', encoding='euc-kr', mode='r+')
            soup = BeautifulSoup(htmlDoc)
        divs = soup.find_all('body')[0].find_all('div')
        title = self.versionTitleInputText.text
        for div in divs:
            div_id = div['id']
            if div_id != None and div_id == 'list_pol':
                p_elements = div.find_all('p')
                p_ele = soup.new_tag('p')
                plistName = ipaName.replace('ipa','plist')
                url = 'itms-services://?action=download-manifest&url=https://apps.infraware.net:9999/download/POL/' + self.majorInputText.text +'/'+plistName
                a_ele = soup.new_tag('a', href=url,title="Download")
                a_ele.string = 'POLARIS Office v' + self.majorInputText.text + ' (' + ipaName[ipaName.find('_')+1:ipaName.rfind('.plist')] + ') - ' + title
                img_ele = soup.new_tag('img',src="./ico_new.png",width="33",**{'class':''})
                p_ele.insert(0,img_ele)
                p_ele.insert(1, a_ele)
                div.insert(0, p_ele)
        html = soup.prettify().encode('euc-kr')
        with open("output.html", "wb") as file:
            file.write(html)
    
class OSXGuiApp(App):
    def build(self):
        return OSXGuiWidget()
    
if __name__ == '__main__':
    OSXGuiApp().run()
