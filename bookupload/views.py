from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from os import mkdir
from pdf2image import convert_from_path
import os
from django.views.decorators.csrf import csrf_exempt
from .models import Book, Object, Stack

# Create your views here.
@csrf_exempt
def uploadBookMain(request):
    result = uploadBook(request)
    if result[0] == True:
        try:
            aFile = request.FILES.get('book')
            book = Book(NAME = aFile.name, SIZE=aFile.size, PATH = result[1])
            stack = Stack(BOOK_id = book.id, )
            print(dir(aFile))
        except Exception as err:
            print('erro:')
            print(err)
        response = JsonResponse({'result': True, 'post-operation': "success"})
        response['Access-Control-Allow-Origin'] = "*"
        return response
    else:
        print(result[1])
        print(result[2])
        response = JsonResponse({ 'result': result[0], 'Error': result[1], 'errorMsg': result[3], 'post-operation': 'fail' })
        response['Access-Control-Allow-Origin'] = "*"
        return response

@csrf_exempt
def uploadBook(request):
    if request.META['HTTP_REFERER'].find("http://localhost:4200/newbook") == -1:
        return [False, None, "Http Refere is non-authorized"]
    if request.method == 'POST':
        print("1 - request method = {0}".format(request.method))
        if request.POST and request.FILES:
            try:
                aFile = request.FILES.get('book')
                if aFile == None:
                    #
                    return [False, None, "Couldn't find the book file"]
                else:
                    print("2 - caught book file")
                    fileType = aFile.content_type
                    if fileType.find("pdf") == -1:
                        return [False, None, "File must be of pdf type"]
                    else:
                        print("3 - book file is a pdf")
                        folderName = aFile.name
                        if folderName.find(".pdf") != -1:
                            folderName = folderName.replace(".pdf", "[_dir_]")
                        else:
                            folderName = folderName + "[_dir_]"
                    try:
                        print("4 - trying to create the main folder")
                        result = createMainFolder(folderName)
                        if result[0] == True:
                            mainFolderPath = result[1]
                            print("5 - created the main folder: {0}".format(mainFolderPath))
                            print("6 - trying to save the book file")
                            result = saveFile(mainFolderPath, aFile)
                            if result[0] == True:
                                pdfPath = result[1]
                                print("7 - saved the file at: {0}".format(pdfPath))
                                print("8 - Trying to create the image folder")
                                result = createImgFolder(mainFolderPath)
                                if result[0] == True:
                                    imgFolderPath = result[1]
                                    print("9 - created the image folder at: {0}".format(imgFolderPath))
                                    print("10 - trying to convert the pdf file to img files.")
                                    result = convertPDF(imgFolderPath, pdfPath)
                                    if result[0] == True:
                                        print("11 - we converted the pdf file at {0} in images".format(imgFolderPath))
                                        return [True, imgFolderPath]
                        return result
                    except Exception as err:
                        return [False, err, "An error has occurred at uploadBook function"]

            except Exception as err:
                return [False, err, "An error has occurred at uploadBook function"]
                
    else:
       return [False, None, "This function only accepts POST requests"]

def createMainFolder(folderName = None):
    if folderName == None or type(folderName) != str:
        return [False, None, "folderName must be of string type"]
    else:
        try:
            mainFolderPath = "/home/rafael/MyLibrary/{0}/".format(folderName)
            mkdir(mainFolderPath)
            return [True, mainFolderPath]
        except FileExistsError as err:
            index = 2
            while True:
                try:
                    path = mainFolderPath.replace("[_dir_]", "[_dir_({0})]".format(index))
                    index += 1
                    print("\t\ttrying to create main fold path at: {0}".format(path))
                    mkdir(path)
                    mainFolderPath = path
                    return [True, mainFolderPath]
                except FileExistsError as e:
                    pass
                except Exception as e:
                    return [False, e, "An error has occurred while trying to create the main folder. last path: {0}".format(mainFolderPath)]
        except Exception as err:
            return [False, err, "An error has occurred while trying to create the main folder. last mainFolderPath: {0}".format(mainFolderPath)]

def createImgFolder(mainFolderPath = None):
    if mainFolderPath == None or type(mainFolderPath) != str:
        return [False, None, "mainFolderPath must be of string type" ]
    else:
        try:
            imgFolderPath = mainFolderPath + "imgs/"
            mkdir(imgFolderPath)
            return [True, imgFolderPath]
        except Exception as err:
            return [False, err, "An error has occurred while trying to create the main folder. imgFolderPath: {0}".format(imgFolderPath)]

def saveFile(mainFolderPath = None, aFile = None):
    if mainFolderPath == None or aFile == None or type(mainFolderPath) != str:
        return [False, None, "type of folderName must be a string and aFile must be an object"]
    else:
        try:
            pdfPath = mainFolderPath + aFile.name
            newFile = open(file = pdfPath, mode='wb')
            data = aFile.read()
            newFile.write(data)
            newFile.close()
            return [True, pdfPath]
        except Exception as err:
            return [False, err, "An error has occurred while writing and saving the new book file"]

def convertPDF(imgFolderPath = None, pdfPath = None):
    if imgFolderPath == None or pdfPath == None or type(imgFolderPath) != str or type(pdfPath) != str:
        return [False, None, "imgFolderPath and pdfPath must be of type str"]
    try:
        inicio = 0
        fim  = 100
        while True:
            lista = convert_from_path(pdf_path = pdfPath, output_folder = imgFolderPath, first_page = inicio, last_page = fim, fmt="jpg")
            
            if len(lista) == 0:
                print("finished converting the pdf file")
                break
            else:
                renameImgs(imgFolderPath, inicio)
                print("\t\tconverted pdf to img from page: {0} to page {1}".format(inicio, fim))
                inicio = fim + 1
                fim = inicio + 50
        return [True,]
    except Exception as err:
        errMsg = "An error has occurred while converting a pdf({0}) to images files".format(pdfPath)
        print(errMsg)
        return [False, err,  errMsg]

def renameImgs(imgFolderPath = None, inicio = None):
    if imgFolderPath == None or type(imgFolderPath) != str:
        return [False, None, "imgFolderPath must be of string type"]
    else:
        try:
            index = inicio
            lista = os.listdir(imgFolderPath)
            lista.sort()
            #Nessa parte pegamos a quantidade de elementos da lista, que é um número, transformamos em uma string e pegamos a quantidade de caracteres.
            length = len(str(len(lista)))
            for img in lista:
                if img.find("-") != -1:
                    newname = formatNumber(index, length)
                    os.rename(src = imgFolderPath + img, dst = imgFolderPath + "{0}.jpg".format(newname))
                    index += 1
            return [True]
        except Exception as err:
            return [False, err, "An error has occurred while trying to rename the imgs at {0}".format()]

def formatNumber(number=None, length=None):
    if number == None or length == None or type(number) != int or type(length) != int:
        return [False, None, "number an length must be of type int"]
    if length <= 0:
        return [False, None, "length must be an integer greater than 0"]
    else:
        try:
            n = str(number)
            while len(n) < length:
                n = '0' + n
            return n
        except Exception as err:
            return [False, None, "An error has occurred while formating a number: {0}".format(number)]
                