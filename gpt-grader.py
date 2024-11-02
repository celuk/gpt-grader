import os
import subprocess
import psutil
import pandas as pd
from openpyxl import load_workbook

import g4f

from g4f.Provider import (
    AItianhu,
    Acytoo,
    Aichat,
    Ails,
    Bard,
    Bing,
    ChatBase,
    ChatgptAi,
    H2o,
    HuggingChat,
    OpenAssistant,
    OpenaiChat,
    Raycast,
    Theb,
    Vercel,
    Vitalentum,
    Ylokh,
    You,
    Yqcloud,
)

## We are using Bing's GPT-4 model
## temperature is between 0 and 1
## 0 means more deterministic, 1 means more creative
g4f.Provider.Ails.temperature = 0

PWD_MAIN = os.getcwd()
os.chdir(PWD_MAIN)

## Excel file that contains students' information
## It should contain 3 columns according to this code, if you want, change it in the code
## Column A should be student's order in the excel
## Column B should be student's number
## Column C should be student's name
## that should match student's folder name case insensitively before first underscore character "_"
## e.g folder names can be "Adam Smith_12345678", "Albert Einstein_12345678" etc.
XL_FILE = "lab_final_fall24.xlsx"

## Upper folder path of students' folders
TOP_PATH= "/home/shc/mdt/fall24/final/ortak"
## e.g. here /home/shc/mdt/guz24/final/ortak folder should contain;
## Adam Smith_12345678
## Albert Einstein_12345678
## ...
## folders and each folder should contain MODULES files
##                                          |
##                                          |
##                                          v

## Verilog, python etc. files
## If there are multiple files to compile or interpret, place one space between them
## Place top module file first if there are multiple files
MODULES = f"example.v"
TOP_MODULE = MODULES.split()[0]
TOP_MODULE_NAME = TOP_MODULE.split(".")[0]

## Module's total point to evaluate
MODULE_POINT = 15

## Language can be verilog, python etc.
LANGUAGE = "verilog"

## Path of iverilog, python3 or any other compiler or interpreter
EXECUTOR_PATH = "iverilog"

TB_EXISTS = True
## If there are testbench, wrapper etc. files
## Here we are using testbench file in TOP_PATH (/home/shc/mdt/guz24/final/ortak) folder
## because it is from us not a student's and same for all students for the same evaluation
if TB_EXISTS:
    TB_MODULES = f"{TOP_PATH}/tb_{TOP_MODULE}"
else:
    TB_MODULES = ""

## Output executable file name of the compiled code if exists
OUT_EXEC = "tb_sim"

DEFAULT_EXEC = "a.out"

## Command to compile or interpret the code
EXEC_CMD = f"{EXECUTOR_PATH} {MODULES} {TB_MODULES} -o {OUT_EXEC}"

## Expected answer codes also should be in TOP_PATH folder like testbenches
answer_file = open(f"{TOP_PATH}/{TOP_MODULE}", "r", errors="ignore")
answer_code = answer_file.read()
answer_file.close()

tb_file = open(f"{TOP_PATH}/tb_{TOP_MODULE}", "r", errors="ignore")
tb_code = tb_file.read()
tb_file.close()

student_ans_code = ""

process_out = ""

result_line = ""

catstr = ""
catstrall = ""

wb = load_workbook(XL_FILE, data_only=True)

## TODO make here language independent
## For now, it is for verilog modules

for sheet in wb:
    for cell1,cell2,cell3 in zip(sheet["A"], sheet["B"], sheet["C"]):
        for file in sorted(os.listdir()):
            file_path = os.path.join(PWD_MAIN, file)
            if os.path.isdir(file_path):
            
                os.chdir(file_path)

                if next(os.walk('.'))[1]:
                    os.chdir(next(os.walk('.'))[1][0])

                student_folder_name = file.split("_")[0]

                if str(cell3.value).lower().strip() == student_folder_name.lower().strip():

                    if os.path.exists(OUT_EXEC):
                        os.remove(OUT_EXEC)
                    if os.path.exists(DEFAULT_EXEC):
                        os.remove(DEFAULT_EXEC)
    
                    v_ext_arr = [f for f in os.listdir() if f.endswith(".v")]
    
                    process_out = ""
                    if len(v_ext_arr) > 0:
                        warns = subprocess.getoutput(EXEC_CMD)
                        try:
                            process = subprocess.Popen(f"./{OUT_EXEC}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            process_out, process_err = process.communicate(timeout=5)
                            process_out = warns + process_out.decode()
    
                        except:
                            parent = psutil.Process(process.pid)
                            for child in parent.children(recursive=True):
                                child.kill()
                            parent.kill()
                            process_out = ""
                            pass

                    print()
                    catstrall += "\n"
                    print("----------------------------------------")
                    catstrall += "----------------------------------------\n"
                    print(str(cell1.value).strip() + " - " + str(int(cell2.value)).strip() + " - " + str(cell3.value).strip())
                    catstrall += str(cell1.value).strip() + " - " + str(int(cell2.value)).strip() + " - " + str(cell3.value).strip()
                    print("--------------------")
                    catstrall += "\n--------------------\n"

                    print("####################")
                    catstrall += "\n####################\n"

                    print(process_out)
                    catstrall += process_out

                    print("####################\n")
                    catstrall += "####################\n\n"

                    print("********************")
                    catstrall += "\n********************\n"

                    response = "sorry"

                    try:
                        studentansfile = open(f"{TOP_MODULE_NAME}.v", "r", errors="ignore")
                        student_ans_code = studentansfile.read()
                        studentansfile.close()

                        gptstr = f"""
                        You are a teacher who is a master in verilog language.

                        You have these strict rules for assesment of codes:
                        - Consider functionality of the student's code. Just you can deduct points for functionality difference, syntax error and different port names. 
                        - Do not deduct any point for naming differences except port names, port names should be exactly same as answer
                        - Do not deduct any point for indendation, comments.
                        - Deduct point if there is no one-to-one functionality.

                        A student should write a code that corresponds one-to-one functionality of this code:

                        // Answer code is below:
                        {answer_code}
                        // End of Answer code

                        And student's code should pass all tests in your testbench.

                        // Your testbench code is below:
                        {tb_code}
                        // End of testbench code

                        // Student's code is below:
                        {student_ans_code}
                        // End of student's code

                        Now, you should rate student's code out of {MODULE_POINT}, according to your answer and testbench codes (consider correctness and functional similarity to the answer code)

                        Write your decided point (at the last line and as a newline) with this format as: "Point: 4/{MODULE_POINT}" means this code gets 4 out of {MODULE_POINT}.
                        """

                        student_ans_code = ""

                        while "sorry" in response:
                            response = g4f.ChatCompletion.create(
                                model=g4f.models.gpt_4,
                                provider=g4f.Provider.Bing,
                                messages=[{"role": "user", "content": gptstr}],
                                temperature=0
                            )
                    except:
                        pass

                    print(response)
                    catstrall += response

                    print("********************")
                    catstrall += "\n********************\n\n"

                    catstr = ""
                    try:
                        catstr = subprocess.run(f"cat {TOP_MODULE_NAME}.v", shell=True, capture_output=True, timeout=2).stdout.decode(errors='ignore')
                    except:
                        pass
                    catstrall += catstr
                    print(catstr)
                    print("----------------------------------------")
                    catstrall += "\n----------------------------------------\n"
                    print()
                
                os.chdir(PWD_MAIN)

## Write all outputs to a text file
## The format is like below:

## ----------------------------------------
## Order in the excel - Number - Name
## --------------------
## ####################
## testbench output if exists
## ####################
## ********************
## output of gpt prompt
## gpt point is in the end of the output
## ********************
##
## code of the student
## ----------------------------------------
## 
## other student is in the same format...
## ...
with open(f"all_with_gpt_{TOP_MODULE_NAME}.txt", "w") as f:
    f.write(catstrall)
