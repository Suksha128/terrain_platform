import re

with open('backend/app/services/terrain_features.py', 'r') as f:
    content = f.read()

bad_block = """    # ADVANCED ACCURACY: Calculate D-Infinity SCA exclusively for highly accurate TWI
    d_inf_sca_path = str(out / "d_inf_sca.tif")
    d_inf_pntr_path = str(out / "d_inf_pointer.tif")
    wbt.d_inf_pointer(dem=paths["conditioned_dtm"], output=d_inf_pntr_path)
    wbt.d_inf_flow_accumulation(
        input=d_inf_pntr_path,
        output=d_inf_sca_path,
        out_type="Specific Catchment Area (SCA)",
        log=False,
        clip=False
    )
    paths["d_inf_sca"] = d_inf_sca_path"""

good_block = """    # ADVANCED ACCURACY: Calculate D-Infinity SCA exclusively for highly accurate TWI
    d_inf_sca_path = str(out / "d_inf_sca.tif")
    wbt.d_inf_flow_accumulation(
        i=paths["conditioned_dtm"],
        output=d_inf_sca_path,
        out_type="sca",
        log=False,
        clip=False,
        pntr=False
    )
    paths["d_inf_sca"] = d_inf_sca_path"""

content = content.replace(bad_block, good_block)

with open('backend/app/services/terrain_features.py', 'w') as f:
    f.write(content)
