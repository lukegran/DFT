
LIB_CELLS_PATH = "../data/library"
MODELSIM_DIR = "../data/modelsim"
MODELSIM_INPUT_DIR = "input" 
MODELSIM_GOLD_DIR = "gold" 
MODELSIM_OUTPUT_DIR = "output" 
VERILOG_DIR = "../data/verilog"
###  VERILOG_DIR = "../data/EPFL" -- deprecated
PATTERN_DIR ="../data/patterns"
# in each modelsim prj directory where inputs will be stored
## TODO for Ting-Yu: read a good description for these constants

FAULT_DICT_DIR = "../data/fault_dict_new"
FAULT_SIM_DIR = "../data/fault_sim"
CKT_DIR = "../data/ckt"
# TEST POINT INSERTION PROBLEM:
HTO_TH = 0.1
HTC_TH = 0.05
STAFAN_B_MIN = 0.0001
STAFAN_C_MIN = 0.001

SAMPLES = 100

V_FORMATS = ["EPFL", "ISCAS85"]

# LOGIC LIBRARY RELATED:
CELL_NAMES = {
        "XOR": ["xor", "XOR2", "XOR2_X1"],
        "XNOR": ["xnor", "XNOR2", "XNOR2_X1"],
        "OR": ["or", "OR2", "OR2_X1", "OR", "OR2_X2", "OR3_X1", "OR4_X1"],
        "NOR": ["nor", "NOR2", "NOR2_X1", "NOR2_X2", "NOR3_X1", "NOR4_X1"],
        "AND": ["and", "AND2", "AND2_X1", "AND", "AND2_X2", "AND3_X1", "AND4_X1"],
        "NAND": ["nand", "NAND2", "NAND2_X2", "NAND3_X1", "NAND4_X1", "NAND2_X1"],
        "NOT": ["not", "inv", "NOT", "INV_X1", "INV_X2", "INV_X4"],
        "BUFF": ["buff", "buf", 
            "CLKBUF_X12", "CLKBUF_X1", "CLKBUF_X2","CLKBUF_X4","CLKBUF_X8","CLKBUF_X16",
            "BUF_X1", "BUF_X2", "BUF_X4", "BUF_X8"]
        }

ALL_ISCAS85=["c17","c432","c499","c880","c1355","c1908","c2670","c3540","c5315","c6288","c7552"] 
ALL_EPFL_EZ=["arbiter", "sin", "bar","dec", "int2float", 
        "multiplier", "cavlc", "adder", "max", "priority", "voter"]
