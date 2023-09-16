from utils.tac.temp import Temp

# virtual/physical register
# A Reg with index > 0 is a virtual register
Reg = Temp


def is_virt_reg(r: Reg) -> bool:
    return r.index > 0


def phys_reg(id: int) -> Reg:
    return Reg(-id)


WORD_SIZE = 4  # in bytes


class GPRegs:  # General Purpose Registers
    ZERO = phys_reg(0)
    RA = phys_reg(1)  # return address
    SP = phys_reg(2)  # stack pointer
    GP = phys_reg(3)  # global pointer
    TP = phys_reg(4)  # thread pointer
    T0 = phys_reg(5)
    T1 = phys_reg(6)
    T2 = phys_reg(7)
    FP = phys_reg(8)  # frame pointer
    S1 = phys_reg(9)
    A0 = phys_reg(10)
    A1 = phys_reg(11)
    A2 = phys_reg(12)
    A3 = phys_reg(13)
    A4 = phys_reg(14)
    A5 = phys_reg(15)
    A6 = phys_reg(16)
    A7 = phys_reg(17)
    S2 = phys_reg(18)
    S3 = phys_reg(19)
    S4 = phys_reg(20)
    S5 = phys_reg(21)
    S6 = phys_reg(22)
    S7 = phys_reg(23)
    S8 = phys_reg(24)
    S9 = phys_reg(25)
    S10 = phys_reg(26)
    S11 = phys_reg(27)
    T3 = phys_reg(28)
    T4 = phys_reg(29)
    T5 = phys_reg(30)
    T6 = phys_reg(31)

    CALLER_SAVED = (T0, T1, T2, T3, T4, T5, T6, A0, A1, A2, A3, A4, A5, A6, A7)
    CALLEE_SAVED = (S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11)
    ALLOCATABLE = CALLER_SAVED + CALLEE_SAVED  # s0 (frame pointer) is not here
    ARGS = (A0, A1, A2, A3, A4, A5, A6, A7)

    COUNT = 32
    MAX_SAVED_COUNT = 13  # ra, s0~s11


GPR_NAMES = (
    "x0",
    "ra",
    "sp",
    "gp",
    "tp",
    "t0",
    "t1",
    "t2",
    "fp",
    "s1",
    "a0",
    "a1",
    "a2",
    "a3",
    "a4",
    "a5",
    "a6",
    "a7",
    "s2",
    "s3",
    "s4",
    "s5",
    "s6",
    "s7",
    "s8",
    "s9",
    "s10",
    "s11",
    "t3",
    "t4",
    "t5",
    "t6",
)


def reg_name(r: Reg) -> str:
    if r.index > 0:
        return "v%d" % r.index
    i = -r.index
    assert 0 <= i < GPRegs.COUNT
    return GPR_NAMES[i]
