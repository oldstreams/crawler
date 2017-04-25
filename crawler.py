#!/usr/bin/env python3

from datetime import date
import sys
import os
import re
import requests
import uuid
import xml.etree.ElementTree as ET

dictCode = {
  'hzrb': {
    'name': '杭州日报',
    'pattern': 'http://hzdaily.hangzhou.com.cn/hzrb/{:%Y/%m/%d/page_list_%Y%m%d}.html',
    'WH' : '644*1024'
  }
}

def getPageList( day, code ):
  url = dictCode[code]['pattern'].format(day)
  resp = requests.get(url)
  resp.encoding = 'utf-8'
  return re.findall( r'href="(http[^"]+\.pdf)".+href="([^"]+\.html)".+>第([^<>]+)版：([^<>]+)<', resp.text, re.MULTILINE )

def savePDF( day, pdfurl, bc ):
  pdfdir = 'PDF/{:%Y/%Y%m%d}/{}'.format(day, bc)
  if not os.path.exists( pdfdir ):
    os.makedirs( pdfdir )
  pdfname = pdfurl.split('/')[-1]
# 目前不支持下载
#  with open(os.path.join(pdfdir, pdfname), 'wb') as of:
#    of.write(requests.get(pdfurl).content)
#  return pdfname
  return ''

def saveJPG( day, imgurl, bc, prefix ):
  imgdir = '{}/{:%Y/%Y%m%d}/{}'.format(prefix, day, bc)
  if not os.path.exists( imgdir ):
    os.makedirs( imgdir )
  imgname = imgurl.split('/')[-1].split('?')[0]
  with open(os.path.join(imgdir, imgname), 'wb') as of:
    of.write( requests.get(imgurl).content)
  return imgname

def saveXML( code, day, bc, et ):
  xmldir = 'xml/{:%Y/%Y%m%d}/{}'.format(day,bc)
  if not os.path.exists( xmldir ):
    os.makedirs( xmldir )
  xmlname = '{}{:%Y%m%d}{}v01h.xml'.format( code.upper(), day, bc )
  et.write( os.path.join(xmldir, xmlname), encoding='utf-8', xml_declaration=True )
  return xmlname

def getZBdict( html ):
  list = re.findall( r'<area .*?coords="(.*?)" href="(.+?)">', html )
  dict = {}
  for item in list:
    dict[item[1]] = item[0]
  return dict

def getMatch( text, pattern ):
  result = re.search(pattern, text, re.MULTILINE|re.DOTALL )
  if( result ):
    return result.group(1)
  else:
    return ''

def getContent( html ):
  c1 = getMatch( html, r'<div class="content">(.*(.*<p>.*</p>.*)*.*)</div>' )
  clist = re.findall( r'<p>(.*?)</p>', c1 )
  content = ''
  for c2 in clist:
    content = content + c2 + '\n'
  return content

def getImages( html ):
  c1 = getMatch( html, r'<div class="content">(.*?)</div>' )
  imglist = re.findall( r'<img src="(.*?)"/>', c1 )
  return imglist

def dealBC( code, day, bc, bm, pageurl ):
  Dayinfo = ET.Element("Dayinfo")
  DescriptionMetaGroup = ET.SubElement( Dayinfo, "DescriptionMetaGroup" )
  RQ = ET.SubElement( DescriptionMetaGroup, 'RQ' )
  RQ.text = '{:%Y-%m-%d}'.format( day )
  MC = ET.SubElement( DescriptionMetaGroup, 'MC' )
  MC.text = dictCode[code]['name']
  NQ = ET.SubElement( DescriptionMetaGroup, 'NQ' )
  QS = ET.SubElement( DescriptionMetaGroup, 'QS' )
  item = ET.SubElement( Dayinfo, "item" )

  pdfname = savePDF( day, pageurl, bc )
  # page_detail_...
  detail = requests.get( 'http://hzdaily.hangzhou.com.cn/{}/{:%Y/%m/%d}/{}'.format( code, day, pageurl ) )
  detail.encoding = 'utf-8'
  viewpage = re.search( r'src="(page_view.*?\.html)"', detail.text ).group(1)
  view = requests.get( 'http://hzdaily.hangzhou.com.cn/{}/{:%Y/%m/%d}/{}'.format( code, day, viewpage ) )
  view.encoding = 'utf-8'
  imgurl = re.search( r'<img src="([^"]+)".*>', view.text ).group(1)
  jpgname = saveJPG( day, imgurl, bc, 'JPG' )
  dictZB = getZBdict( view.text ) #获取Url与坐标的映射
  # article_list_...
  articlelistfile = getMatch( detail.text, r'src="(article_list_.*?\.html)"' )
  articlelist = requests.get( 'http://hzdaily.hangzhou.com.cn/{}/{:%Y/%m/%d}/{}'.format( code, day, articlelistfile ) )
  articlelist.encoding = 'utf-8'
  titlelist = re.findall( r'<li><a href="(.+?)".*?>(.+?)</a></li>', articlelist.text, re.MULTILINE )

  for title in titlelist:
    MetaInfo = ET.SubElement( item, "MetaInfo" )
    KY = ET.SubElement( MetaInfo, "KY" )
    KY.text = str(uuid.uuid4())
    GJID = ET.SubElement( MetaInfo, "GJID" )
    GJID.text = str(uuid.uuid4())
    BC = ET.SubElement( MetaInfo, "BC" )
    BC.text = bc
    BM = ET.SubElement( MetaInfo, "BM" )
    BM.text = bm
    ZB = ET.SubElement( MetaInfo, "ZB" )
    ZB.text = dictZB[title[0]] # 还需要处理
    Url = ET.SubElement( MetaInfo, "Url" )
    Url.text = 'http://hzdaily.hangzhou.com.cn/{}/{:%Y/%m/%d}/{}'.format( code, day, title[0] )
    article = requests.get( Url.text )
    article.encoding = 'utf-8'
    BT = ET.SubElement( MetaInfo, "BT" )
    BT.text = getMatch( article.text, r'<h1>(.*?)</h1>' )
    FB = ET.SubElement( MetaInfo, "FB" )
    FB.text = getMatch( article.text, r'<h2>(.*?)</h2>' )
    YT = ET.SubElement( MetaInfo, "YT" )
    YT.text = getMatch( article.text, r'<h3>(.*?)</h3>' )
    XB = ET.SubElement( MetaInfo, "XB" )
    TX = ET.SubElement( MetaInfo, "TX" )
    TX.text = getContent( article.text )
    ZY = ET.SubElement( MetaInfo, "ZY" )
    QY = ET.SubElement( MetaInfo, "QY" )
    HJ = ET.SubElement( MetaInfo, "HJ" )
    ZZ = ET.SubElement( MetaInfo, "ZZ" )
    CBZZ = ET.SubElement( MetaInfo, "CBZZ" )
    BJ = ET.SubElement( MetaInfo, "BJ" )
    FL = ET.SubElement( MetaInfo, "FL" )
    FBLX = ET.SubElement( MetaInfo, "FBLX" )
    WZBJ = ET.SubElement( MetaInfo, "WZBJ" )
    TC = ET.SubElement( MetaInfo, "TC" )
    LM = ET.SubElement( MetaInfo, "LM" )
    CBBM = ET.SubElement( MetaInfo, "CBBM" )
    BJBM = ET.SubElement( MetaInfo, "BJBM" )
    WJLX = ET.SubElement( MetaInfo, "WJLX" )
    QYR = ET.SubElement( MetaInfo, "QYR" )
    GG = ET.SubElement( MetaInfo, "GG" )
    BJLX = ET.SubElement( MetaInfo, "BJLX" )
    TP = ET.SubElement( MetaInfo, "TP" )
    TPinfo = ET.SubElement( MetaInfo, "TPinfo" )
    Source = ET.SubElement( TPinfo, "Source" )
    JP = ET.SubElement( Source, "JP" )
    JP.text = jpgname
    PD = ET.SubElement( Source, "PD" )
    PD.text = pdfname
    WH = ET.SubElement( Source, "WH" )
    WH.text = dictCode[code]['WH']
    Imageinfo = ET.SubElement( MetaInfo, "Imageinfo" )
    images = getImages( article.text )
    for image in images:
      name = saveJPG( day, image, bc, 'xml' )
      Contnet = ET.SubElement( Imageinfo, "Contnet")  # 拼写有错？？？
      CT = ET.SubElement( Contnet, "CT" )
      CT.text = name
      TS = ET.SubElement( Contnet, "TS" )
      TZ = ET.SubElement( Contnet, "TZ" )
  saveXML( code, day, bc, ET.ElementTree(Dayinfo) )

def main():
  if len(sys.argv)==1 :
    day = date.today()
  else:
    groups = re.match( r'(\d{4})(\d{2})(\d{2})', sys.argv[1] ).groups()
    day = date( int(groups[0]), int(groups[1]), int(groups[2]) )
  code = 'hzrb'

  pagelist = getPageList( day, code ) # 获得版面页面列表
  for i in range(len(pagelist)):
    BC = pagelist[i][2]
    BM = pagelist[i][3]
    dealBC( code, day, BC, BM, pagelist[i][1] )


main()
    

