import os
import os.path
from os.path import basename
from urllib import urlopen
from urlparse import urlparse
import subprocess
from subprocess import Popen, PIPE
import urllib
import shutil
import glob
# custom Lisa module
import clusterfunc

#1. Get data from spreadsheet

def get_data(thefile):
    count=0
    url_data={}
    with open(thefile,"rU") as inputfile:
        headerline=next(inputfile).split(',')
	#print headerline        
        position_name=headerline.index("ScientificName")
        position_reads=headerline.index("Run")
        position_ftp=headerline.index("download_path")
        for line in inputfile:
            line_data=line.split(',')
            name="_".join(line_data[position_name].split())
            read_type=line_data[position_reads]
            ftp=line_data[position_ftp]
            name_read_tuple=(name,read_type)
            print name_read_tuple
            #check to see if Scientific Name and run exist
            if name_read_tuple in url_data.keys():
                #check to see if ftp exists
                if ftp in url_data[name_read_tuple]:
                    print "url already exists:", ftp
                else:
                    url_data[name_read_tuple].append(ftp)
            else:
                url_data[name_read_tuple] = [ftp]
        return url_data

#2. Download data
#(already checked if file exists)

def download(url,newdir,newfile):
    filestring=newdir+newfile
    urlstring="wget -O "+newdir+newfile+" "+url
    #Note: only for Python 3
    #urllib.request.urlretrieve(url,filestring)
    #Use this for Python 2
    s=subprocess.Popen(urlstring,shell=True)
    s.wait()
    print "Finished downloading from NCBI."

#3. Extract with fastq-dump (sratools)
    
def sra_extract(newdir,filename):
    #if seqtype=="single":
    #    sra_string="fastq-dump -v "+newdir+file
    #    print sra_string
    #elif seqtype=="paired":
	# check whether .fastq exists in directory
    if glob.glob(newdir+"*.fastq"):
    	print "SRA has already been extracted", filename
    else:
    	sra_string="fastq-dump -v -O "+newdir+" --split-3 "+newdir+filename
    	#print sra_string
	print "extracting SRA..."
    	s=subprocess.Popen(sra_string,shell=True,stdout=PIPE)
    	s.wait()
	print "Finished SRA extraction."

#4. Generate fastqc from all fastq in directory

def fastqc_report(fastq_file_list,newdir,fastqcdir,filename):
    # imports list of files in each directory
    print fastq_file_list
    print fastqcdir+filename
    if glob.glob(fastqcdir+filename+"_*_fastqc.zip"):
	print "fastqc already complete:",filename
    else:		
    	# creates command to generate fastqc reports from all files in list 
    	file_string=str(fastq_file_list)
    	#print fastq_file_list
    	file_string=" ".join(fastq_file_list)
    	#print file_string
    	fastqc_string="fastqc -o "+fastqcdir+" "+file_string
    	print fastqc_string
    	print "fastqc reports generated for: "+str(fastq_file_list)
    	s=subprocess.Popen(fastqc_string,shell=True)
    	s.wait()

#5. For pipeline testing only:
#   create subset of 1,000,000 reads for each file

def subset_reads(newdir,subsetdir):
    listoffiles=os.listdir(newdir)
    for i in listoffiles:
	if i.endswith(".fastq"):
		newfilename=subsetdir+i[:-6]+".subset1m.fastq"
    		if os.path.isfile(newfilename):
			print "File has already been subsetted:",newfilename
    		else:	
    			subset_string="head -4000000 "+newdir+i+" > "+newfilename
    			print subset_string
    			s=subprocess.Popen(subset_string,shell=True,stdout=PIPE)
    			s.wait()
			print "Finished subsetting."
   
#6. Create symbolic link from data files to working directory

def sym_link(newdir):
    listoffiles=os.listdir(newdir)
    for i in listoffiles:
    	if i.endswith(".subset100k.fastq"):
    		symlink_string="ln -fs "+newdir+i+" /mnt/mmetsp/"+i
		print symlink_string
	    

# this is the main function to execute

def execute(basedir,url_data):
    for item in url_data.keys():
        #Creates directory for each file to be downloaded
        #Directory will be located according to organism and read type (single or paired)
        organism=item[0]
        seqtype=item[1]
        org_seq_dir=basedir+organism+"/"
	print org_seq_dir
	clusterfunc.check_dir(org_seq_dir)
        url_list=url_data[item]
        for url in url_list:
            filename=basename(urlparse(url).path)
            print filename
            newdir=org_seq_dir+filename+"/"
            clusterfunc.check_dir(newdir)
	    fastqcdir=newdir+"fastqc/"
	    clusterfunc.check_dir(fastqcdir)
            #check to see if filename exists in newdir
            if filename in os.listdir(newdir):
               print "sra exists:",filename
            else:        
               print "file will be downloaded:",filename
	       download(url,newdir,filename)
            sra_extract(newdir,filename)
            fastqc(newdir,fastqcdir,filename)
            #subset_reads(newdir,subsetdir)
 	    #fastqc(subsetdir,subsetfastqcdir,filename)

def fastqc(newdir,fastqcdir,filename):
	listoffiles=os.listdir(newdir)
        print listoffiles
        fastq_file_list=[]
   	for i in listoffiles:
		if i.endswith(".fastq"):
			fastq_file_list.append(newdir+i)
	fastqc_report(fastq_file_list,newdir,fastqcdir,filename)         

# use this in case you make a mistake and need to delete a bunch of files:
def delete_files(newdir):
	listoffiles=os.listdir(newdir)
        print listoffiles
	for i in listoffiles:
		if i.endswith(".subset100k.fastq"):
			os.remove(newdir+i)
			print "File removed:",newdir+i

datafile="MMETSP_SRA_Run_Info_subset_d.csv"
basedir="/mnt/mmetsp/"
clusterfunc.check_dir(basedir)
url_data=get_data(datafile)
print url_data
execute(basedir,url_data)

