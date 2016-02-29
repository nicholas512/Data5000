%run "/Users/Nick/Desktop/Inversion/Git/Geotop/geotop_interaction.py"

MTD = list()
for i in range(1,1001):
    url = 'http://aps.ngu.no/pls/oradb/minres_pe_fakta.pe_mtd?p_id=%s&p_spraak=E' %str(i)
    MTD.append(url)

BOHO = list()
for i in range(1,1001):
    url = 'http://aps.ngu.no/pls/oradb/minres_bo_fakta.boho?p_id=%s&p_spraak=E' %str(i)
    BOHO.append(url)
    
F.Trawl(startID=2,fileList=MTD,datatype="Minilogger")

F.Trawl(startID=2,fileList=MinBO,datatype="Borehole")