#-------------------------------------------------------------------------------
# Name:        ReSort
# Author:      Denys Lozinskyi
# Version:     v. 2.3.9  (RC)
# ------------------------------------------------------------------------------

import os
import re
import zipfile
from shutil import move, copy2
from xml.etree.ElementTree import XML

from tkinter import *
from tkinter import filedialog, ttk

from PIL import ImageTk, Image


def get_docx_text(path):
    """
       Модуль извлекает текст из MS XML Word document (.docx) и превращает его строку в формате Unicode.
       Разработчик ядра модуля: Etienne, http://etienned.github.io/posts/extract-text-from-word-docx-simply/
       Адаптировано для парсинга по docx и ReSort: Денис Лозинский
    """
    # ниже - переменные, необходимые для docx парсинга, поскольку файлы docx представляют из себя заархивированные namespaced XML
    word_namespace = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    para = word_namespace + 'p'
    text = word_namespace + 't'

    document = zipfile.ZipFile(path)
    xml_content = document.read('word/document.xml')
    document.close()
    tree = XML(xml_content)    

    paragraphs = []
    for paragraph in tree.iter(para):
        texts = [node.text for node in paragraph.iter(text) if node.text]        
        if texts:
            paragraphs.append(''.join(texts))
    joint_text = ' '.join(paragraphs)
    joint_text = joint_text.lower()  # нужно для корректной работы title_maker 
    result_list = re.findall(r'\w+', joint_text)  # на выходе имеем список слов без пробелов и знаков препинания в формате юникод
        
    return result_list


def is_dpk(file):
    '''
       функция проверяет, является ли file типом ДПК. Слова-маркеры разделены на группы.
       Файл ДПК отличает то, что в нем присутствуют слова из каждой из указанных групп.
       Группы маркеров можно добавлять, если необходимо
    '''
    
    markers = (("справка", "reference", "βεβαιωσις"),
               ("каноничным", "canonically", "κανονικώς"),
               ("клириком", "clergyman", "χειροτονημένος"),
               ("священнодействовать", "ministering", "ιεροπράττει"),
               ("церкви", "church", "εκκλησίας"))

    for i in range(len(markers)):
        control = 0
        for j in range(len(markers[i])):
            if markers[i][j] in file:
                #print(markers[i][j])
                control += 1
        #print(control)
        '''
           control увеличивается на единицу при совпадении слов с каждым отдельным вложенным кортежем,
           что обуславливает продолжение итерации верхнего уровня, и обнуляется при каждом переходе к следующему вложенному кортежу.
           Таким образом, несовпадение с хотя бы одним из вложенных кортежей делает control равным нулю и возвращает False.
           Если с каждым из кортежей совпадение есть, возвращаем True
        '''
        if control == 0:
            return False
    return True


def title_maker(file):
    '''
       функция принимает файл дпк, находит в нем имя и фамилию того, кому выдана справка,
       и возвращает строку в формате Имя Фамилия, о каноничности.docx
       Если в целевой папке имя уже присутствует, возвращает (с помощью if_dublicate_title) имя и фамилию в формате:
       Михаил Васнецов(n).docx. Если имя в файле найти не удалось, возвращает default_name(n).docx
    '''
    
    default_name = 'справка о каноничности.docx' 
    for i in range(len(file)):
        #print(file[i])        
        if file[i] == 'свидетельствуем':
            name = str(file[i+3])
            if file[i+5] == 'миру':
                surname = str(file[i+7])
            else:
                surname = str(file[i+4])
        elif file[i] == 'certify':
            name = str(file[i+3])
            if file[i+5] == 'name':
                surname = str(file[i+7])
            else:
                surname = str(file[i+4])
        elif file[i] == 'βεβαίωσιν':
            name = str(file[i+2])
            if file[i+4] == 'κόσμον':
                surname = str(file[i+6])
            else:
                surname = str(file[i+3])        
    try:                    
        title = name.capitalize() + ' ' + surname.capitalize() + ', о каноничности.docx'
        #print(title)
        #print(os.listdir(PATH2DEST_FOLDER))
    except:
        '''
           если имя и фамилию определить не удалось (слова-маркеры для индексации фамилии и имени отсутствуют
           или написаны с ошибками), установить имя по умолчанию. Потом проверить, есть ли файл с таким именем в папке
        '''
        title = default_name
    if title in os.listdir(PATH2DEST_FOLDER):
        return if_dublicate_title(title)
    else:
        display2.insert(END, title)
        display2.yview(END)  # следить за скроллом, при необходимости - удалить
        window.update_idletasks()
        return title

        
def if_dublicate_title(file_name):
    '''
       функция вызывается из title_maker в случае, если файл с таким именем уже присутствует в папке назначения.
       Функция возвращает принимаемое имя файла с его расширением в формате ИМЯ(n).расширение,
       где n - нумератор повторений имени файла, целое число, начиная с 2,
       соответствующее количеству повторений имени файла в папке
    '''
    
    title_constructor = file_name.split('.')  # отделяем имя файла от расширения, попутно образовывая список
    title_constructor.append(1)  # добавляем в список нумератор повторений
    #print(title_constructor)
    while file_name in os.listdir(PATH2DEST_FOLDER):  # до тех пор, пока файл с таким именем присутствует в папке
        title_constructor[2] += 1  # увеличиваем нумератор на единицу
        # собираем новое имя файла и снова отдаем его на проверку
        file_name = ('%s' + '(%s).' + '%s') %(title_constructor[0], title_constructor[2], title_constructor[1])
    display2.insert(END, file_name)
    display2.yview(END)  # следить за скроллом, при необходимости - удалить
    window.update_idletasks()
    return file_name


def ReSort():
    """
       Главная функция
    """
    try:
        files_to_scan = os.listdir(PATH2SOURCE_FOLDER)
    except:
        status.config(text=">>>>> Сначала выберите папку для анализа")
        return
    else:
        if PATH2SOURCE_FOLDER == "/":  # в переменной сохраняется слеш после сброса кнопкой Сброс. Слеш - условность
           status.config(text=">>>>> Выберите папку для анализа")
           return

    try:
        if PATH2DEST_FOLDER == "/":  # в переменной сохраняется слеш после сброса кнопкой Сброс. Слеш - условность
            status.config(text=">>>>> Выберите папку для перемещения/копирования")
            return
    except:        
        status.config(text=">>>>> Выберите папку для перемещения/копирования")
        return

    
    display1.delete(0, END)  # очищаем дисплеи
    display2.delete(0, END)
    progress["maximum"] = len(files_to_scan)  # устанавливаем верхний порог для прогрессбара - количество файлов в папке
    progress_value = 0  # начальное значение прогрессбара

    # сканируем каждый файл из списка
    dpk_count = 0  # устанавливаем счетчик ДПК
    status.config(text=(">>>>> Обработка..."))
    for document in files_to_scan:
        progress_value += 1  # увеличиваем начальное значение прогрессбара для вычисления дельты
        progress["value"] = progress_value
        progress.update()  # обновление прогрессбара
        # расчет и вывод прогресса выполнения в процентах
        percentage.config(text=str(int((progress_value / progress["maximum"]) * 100)) + " %")
        if document[-5:] == ".docx":            
            #print(document)
            file = get_docx_text(PATH2SOURCE_FOLDER + document)   
            #print(file)
            if is_dpk(file):
                dpk_count += 1
                display1.insert(END, document)
                display1.yview(END)  # следить за скроллом, при необходимости - удалить
                window.update_idletasks()  # необходим, чтобы строки выводились по мере выполнения программы, а не все сразу в конце
                if var.get() == 0:
                    move(PATH2SOURCE_FOLDER + document, PATH2DEST_FOLDER + title_maker(file))  # перемещение файла в папку с переименованием
                elif var.get() == 1:
                    copy2(PATH2SOURCE_FOLDER + document, PATH2DEST_FOLDER + title_maker(file))  # копирование файла в папку с переименованием
            '''
               перемеименование лучше совместить с перемещением (благо, shutil.move это позволяет, т.к. сам использует os.rename)
               поскольку если перед перещением в папке назначения уже будет присутствовать файл с таким же именем,
               move сгенерирует ошибку. Обезопаситься от ошибки можно только перемещением файла с уникальным именем.
               Эту уникальность обеспечит title_maker, работающий совместно с if_dublicate_title
            '''
            #else:
                #print(document + ' - не ДПК')
    if dpk_count == 0:
        status.config(text=">>>>> В выбранной папке файлы ДПК отсутствуют")
    else:
        status.config(text=(">>>>> Процесс завершен. Было обнаружено и каталогизировано " + str(dpk_count) + " ДПК"))
    return


def source_folder():
    """
       как оказалось на практике, askfordirectory возвращает "/" каждый раз
       при нажатии на кнопку "Отмена" в диалоговом окне, что переписывало пути
       в глобальных переменных. Т.е., ты выбрал папку, нажал на кнопку еще раз, но вместо
       выбора нажал "отмену" и путь превратился в слэш, дальше нужно выбрать путь заново.
       Чтобы это предотвратить, решил ввести дополнительные переменные pre_path_s, которые
       сохраняют то, что возвращает askfordirectory, и передают значение в глобальную
       переменную, если значение не равно слэшу. Если же значение равно слэшу (была нажата отмена),
       программа не меняет глобальные переменные. Таким образом в глобальных переменных слэши появляются
       только после очистки экранов с all_clear. Делать глобалки равными пустой строке нельзя,
       потому что несмотря на то, что os.listdir("") выдаст ошибку, os.startfile("") в jump-ах откроет
       окно корневого каталога, а нам нужна ошибка для обработки
    """
    global PATH2SOURCE_FOLDER
    pre_path_source = (filedialog.askdirectory(title = "Выберите папку для анализа") + "/")
    if pre_path_source != "/":
        PATH2SOURCE_FOLDER = pre_path_source
        status.config(text=(">>>>> Папка для анализа:    " + PATH2SOURCE_FOLDER))
        status_source.config(text=PATH2SOURCE_FOLDER)
    return

def dest_folder():
    global PATH2DEST_FOLDER
    pre_path_dest = (filedialog.askdirectory(title = "Выберите папку для перемещения/копирования") + "/")
    if pre_path_dest != "/":
        PATH2DEST_FOLDER = pre_path_dest
        status.config(text=(">>>>> Папка для перемещения/копирования:    " + PATH2DEST_FOLDER))
        status_dest.config(text=PATH2DEST_FOLDER)
    return
        

def jumptosource():
    try:
        os.startfile(PATH2SOURCE_FOLDER)
    except:
        status.config(text=">>>>> Вы не выбрали папку для анализа")
        
def jumptodest():                      
    try:
        os.startfile(PATH2DEST_FOLDER)
    except:
        status.config(text=">>>>> Вы не выбрали папку назначения")


def about():
    if is_opened.get() == 0:  # если окно пока не создано - создать
        global info  # если оставить локальной, блок else не отработает корректно
        info = Toplevel()
        info.geometry("600x350+480+50")
        info.resizable(False, False)
        info.title("О программе")
        info.config(bg="#BDBDBD")
        info.protocol("WM_DELETE_WINDOW", destroy_info)  # если окно будет закрываться с windows - перейти на destroy_info
        content=Label(info, text="Программа Reference Sorting Tool (ReSort™)\nпредназначена \
для автоматизации поиска и каталогизации документов ДПК.\nПрограмма осуществляет поиск ДПК в формате .docx \
на греческом, английском и русском языках в заданной пользователем директории\nи автоматически \
перемещает/копирует их в выбранный пользователем каталог.\nВ процессе переноса/копирования программа \
автоматически переименовывывает все найденные ДПК в формат: 'Имя Фамилия, тип.docx'.\nИмя и фамилию \
для переименования программа извлекает\nиз каждого отдельного документа.\n \
Если имя и фамилию определить не удалось,\nпрограмма установит имя по-умолчанию - 'тип.docx'.\n \
В случае повторения имени файла в целевой папке, к нему будет добавлен нумератор повторений.\n\n \
Разработчик: Денис Лозинский\n2018", font=("Times New Roman", 12), bg="#E6E0F8", relief=SUNKEN, wraplength=560)
        content.pack(fill=BOTH, expand=True)
        is_opened.set(1)  # помечаем окно созданным
    else:
        destroy_info()  # если окно уже создано - закрыть

    
def destroy_info():
    # закрывает окно "о программе" и обнуляет маркер is_opened
    info.destroy()
    is_opened.set(0)
    

def all_clear():
    display1.delete(0, END)
    display2.delete(0, END)
    progress["value"] = 0  # обнуление и очистка прогрессбара
    status_source.config(text="")
    status_dest.config(text="")
    percentage.config(text="")
    global PATH2SOURCE_FOLDER
    PATH2SOURCE_FOLDER = "/"
    global PATH2DEST_FOLDER
    PATH2DEST_FOLDER = "/"
    status.config(text=">>>>> Выберите папки для анализа и каталогизации")


def BothScroll(*args):
    # обеспечивает одновременный скроллинг листбоксов одним скроллером
    display1.yview(*args)
    display2.yview(*args)

def WithMouseWheel(event):
    # обеспечивает одновременный скроллинг листбоксов колесиком мыши
    display1.yview("scroll", int(-1*(event.delta/120)),"units")
    display2.yview("scroll", int(-1*(event.delta/120)),"units")
    # this prevents default bindings from firing, which
    # would end up scrolling the widget twice
    return "break"       

window = Tk()
general_bg = "#1D2129"  # цвет общего фона
displays_bg = "#F5F6CE"  # цвет фона дисплеев
window.title("ReSort build 2.3.9")
window.geometry("1366x768")
window.configure(bg=general_bg)
window.iconbitmap("ReSort.ico")


logo = Label(window, text="ReSort", bg=general_bg, fg="white", font=("Brush Script MT", 32))
logo.place(x=40, y=5)
info = Label(window, text="Reference Sorting Tool", bg=general_bg, fg="white", font=("Times New Roman", 8, "italic"))
info.place(x=80, y=50)

scrollbar = Scrollbar(window, orient="vertical", command=BothScroll)
scrollbar.pack(side=RIGHT, fill=Y)

display1 = Listbox(window, width=55, height=25, bd=2, bg=displays_bg, font=("Times New Roman", 12), \
                   exportselection=0, yscrollcommand=scrollbar.set)
display1.place(x=300, y=90)
display1.bind("<MouseWheel>", WithMouseWheel)

display2 = Listbox(window, width=55, height=25, bd=2, bg=displays_bg, font=("Times New Roman", 12), yscrollcommand=scrollbar.set)
display2.place(x=825, y=90)
display2.bind("<MouseWheel>", WithMouseWheel)

arrow = Label(window, text="⇒", bg=general_bg, fg="white", font=("Times New Roman", 32))
arrow.place(x=762, y=325)

button_source = Button(window,text="Выберите папку для анализа", padx="15", pady="20", relief=RIDGE, command=source_folder)
button_source.place(x=40, y=90)

button_dest = Button(window,text="Выберите папку назначения", padx="16", pady="20", relief=RIDGE, command=dest_folder)
button_dest.place(x=40, y=165)

var=IntVar()
var.set(0)
move_but = Radiobutton(window, text="Переместить", bg=general_bg, selectcolor=general_bg, fg="white", \
                       activebackground=general_bg, activeforeground=displays_bg, variable=var, value=0)
copy_but = Radiobutton(window, text="Только копировать", bg=general_bg, selectcolor=general_bg, fg="white", \
                       activebackground=general_bg, activeforeground=displays_bg, variable=var, value=1)
move_but.place(x=50, y=245)
copy_but.place(x=50, y=275)

button_start = Button(window, text="Начать", padx="20", pady="20", relief=RIDGE, command=ReSort)
button_start.place(x=95, y=325)

button_jumptosource = Button(window, text="Перейти", padx="50", pady="10", relief=RIDGE, command=jumptosource)
button_jumptosource.place(x=445, y=605)

button_jumptodest = Button(window, text="Перейти", padx="50", pady="10", relief=RIDGE, command=jumptodest)
button_jumptodest.place(x=970, y=605)

status = Label(window, text=">>>>> Добро пожаловать в ReSort! Где будем искать файлы?", font=("Times New Roman", 12), \
               height=1, bg="#E6E0F8", relief=RIDGE, padx=5, pady=5, anchor=W)
status.pack(side=BOTTOM, fill=X)

status_source = Label(window, font=("Times New Roman", 10, "italic"), bg=general_bg, fg="white", width=63)
status_source.place(x=300, y=68)

status_dest = Label(window, font=("Times New Roman", 10, "italic"), bg=general_bg, fg="white", width=63)
status_dest.place(x=825, y=68)

is_opened = IntVar()  # переменная-маркер, указывающая на статус окна "О программе"
is_opened.set(0)  # 0 - не создано, 1 - создано
info_button = Button(window, text="Info", font=("Brush Script MT", 24), fg="white", width=4, height=1, bg=general_bg, \
                     activeforeground="#E6E0F8", activebackground=general_bg, relief=FLAT, command=about)
info_button.pack(side=TOP, anchor=E, padx=5, pady=5)

clear_button = Button(window, text="Cброс", font=("Times New Roman", 8, "italic"), bg="#ECCEF5", padx="10", pady="1", \
                      relief=RIDGE, command=all_clear)
clear_button.place(x=758, y=603)

progress = ttk.Progressbar(window, orient="horizontal", mode="determinate")
progress.place(in_=status, relx=0.835, rely=0.02, relwidth=0.165, relheight=0.99)

percentage = Label(window, font=("Times New Roman", 10), bg="#E6E0F8")
percentage.place(in_=status, relx=0.805, rely=0.15)

img=ImageTk.PhotoImage(Image.open("logo.png"))
panel=Label(window, image=img, bg=general_bg)
panel.place(x=75, y=440)

window.mainloop()
