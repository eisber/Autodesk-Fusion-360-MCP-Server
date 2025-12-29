"""Export functions for Fusion 360.

This module contains functions for exporting models to STEP and STL formats.
"""

import adsk.core
import adsk.fusion
import traceback
import os


def export_as_step(design, ui, name):
    """
    Exports the design as a STEP file.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        name: Name for the export file/folder
    """
    try:
        exportMgr = design.exportManager
              
        directory_name = "Fusion_Exports"
        file_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        export_dir_path = os.path.join(file_path, directory_name, name)
        os.makedirs(export_dir_path, exist_ok=True)
        
        stepOptions = exportMgr.createSTEPExportOptions(
            export_dir_path + f'/{name}.step'
        )
        
        res = exportMgr.execute(stepOptions)
        if res:
            if ui:
                ui.messageBox(f"Exported STEP to: {export_dir_path}")
        else:
            if ui:
                ui.messageBox("STEP export failed")
    except:
        if ui:
            ui.messageBox('Failed export_as_step:\n{}'.format(traceback.format_exc()))


def export_as_stl(design, ui, name):
    """
    Exports the design as STL files.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        name: Name for the export folder
    """
    try:
        rootComp = design.rootComponent
        exportMgr = design.exportManager

        stlRootOptions = exportMgr.createSTLExportOptions(rootComp)
        
        directory_name = "Fusion_Exports"
        file_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        export_dir_path = os.path.join(file_path, directory_name, name)
        os.makedirs(export_dir_path, exist_ok=True)

        printUtils = stlRootOptions.availablePrintUtilities

        # Export to print utility
        for printUtil in printUtils:
            stlRootOptions.sendToPrintUtility = True
            stlRootOptions.printUtility = printUtil
            exportMgr.execute(stlRootOptions)

        # Export occurrences
        allOccu = rootComp.allOccurrences
        for occ in allOccu:
            occ_name = export_dir_path + "/" + occ.component.name
            stlExportOptions = exportMgr.createSTLExportOptions(occ, occ_name)
            stlExportOptions.sendToPrintUtility = False
            exportMgr.execute(stlExportOptions)

        # Export bodies
        allBodies = rootComp.bRepBodies
        for body in allBodies:
            body_name = export_dir_path + "/" + body.parentComponent.name + '-' + body.name
            stlExportOptions = exportMgr.createSTLExportOptions(body, body_name)
            stlExportOptions.sendToPrintUtility = False
            exportMgr.execute(stlExportOptions)
            
        if ui:
            ui.messageBox(f"Exported STL to: {export_dir_path}")
    except:
        if ui:
            ui.messageBox('Failed export_as_stl:\n{}'.format(traceback.format_exc()))
