B_efectiva = B / 2 if dividirb_var.get() else B

if blindado and not transposto:
    SDisCond = (A * L * 2) / 100
    SDisConv = (A + B_efectiva) * L * 2 / 100

elif blindado and transposto:
    SDisCond = (A * L * 2) / 100
    SDisConv = (A + B_efectiva) * L * 2 / 100
