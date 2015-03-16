'''
Created on Mar 3, 2015

@author: qurban.ali
'''
import pymel.core as pc
import appUsageApp
import csv
import os
osp = os.path
import qutil

rootPath = osp.dirname(osp.dirname(__file__))
__title__ = 'Setup HumanIK'

def getGoodNodes(node, names, split=False):
    goodNodes = []
    if split:
        if qutil.getNiceName(node.name()).split('_')[-1] in names:
            goodNodes.append(node)
    else:
        if qutil.getNiceName(node.name()) in names:
            goodNodes.append(node)
    children = node.getChildren()
    for child in children:
        goodNodes.extend(getGoodNodes(child, names, split))
    return goodNodes

def setup():
    try:
        data = qutil.getCSVFileData(osp.join(rootPath, "Advance_Skeleton_MoCap.csv"))
        
        # get humanIK children
        zipedData = zip(*data)
        selectedNodes = pc.ls(sl=True)
        humanIK = getGoodNodes(selectedNodes[0], [name[0].split('_')[-1] for name in data], True)
        
        # get rig joints
        #rigJoints = getGoodNodes(pc.ls(sl=True)[1], [name[1] for name in data])
        pc.select(selectedNodes[1])
        rigJoints = [x.firstParent() for x in pc.ls(sl=True, dag=True, type='joint')
                      if qutil.getNiceName(x.firstParent().name()) in zipedData[1]]
        
        # get rig controls
        rigControls = [x.firstParent() for x in pc.ls(sl=True, dag=True, type='nurbsCurve')
                        if qutil.getNiceName(x.firstParent().name()) in zipedData[3]]
        
        # scale the joints down
        pc.select(selectedNodes[0])
        for node in pc.ls(type='joint'):
            node.radius.set(0.25)
        
        pc.select(selectedNodes)
        
        for hNode in humanIK:
            for record in data:
                if record[0].split('_')[-1] == qutil.getNiceName(hNode.name()).split('_')[-1]:
                    break
            rigJoint = record[1]; constraint = record[2]
            for rigJointNode in rigJoints:
                if rigJoint == qutil.getNiceName(rigJointNode.name()):
                    break
            pc.move(hNode, rigJointNode.getRotatePivot(space='world'), a=True, ws=True)
    
        for hNode in humanIK:
            for record in data:
                if record[0].split('_')[-1] == qutil.getNiceName(hNode.name()).split('_')[-1]:
                    break
            rigControl = record[3]; constraint = record[2]
            for rigControlNode in rigControls:
                if rigControl == qutil.getNiceName(rigControlNode.name()):
                    break
            if constraint.lower() == 'parent':
                pc.parentConstraint(hNode, rigControlNode, mo=True)
            elif constraint.lower() == 'orient':
                pc.orientConstraint(hNode, rigControlNode, mo=True)
        # set FKIKBlend to 0
        pc.select(selectedNodes[1])
        for ctrl in [x.firstParent() for x in pc.ls(sl=True, dag=True, type='nurbsCurve')]:
            if qutil.getNiceName(ctrl.name()).lower() in ["FKIKLeg_L".lower(), "FKIKLeg_R".lower()]: 
                ctrl.FKIKBlend.set(0)
        pc.select(selectedNodes)
        
        appUsageApp.updateDatabase('setupHIK')
    except Exception as ex:
        pc.confirmDialog(title=__title__, m=str(ex), button='Ok')