import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from DICOMLib import DICOMUtils
import logging

invalidShItemID = slicer.vtkMRMLSubjectHierarchyNode.GetInvalidItemID()

# -----------------------------------------------------------------------------
# Snippets for testing/debugging
# - Access logic
# pl = slicer.modules.segmentregistration.widgetRepresentation().self().logic

#
# -----------------------------------------------------------------------------
# SegmentRegistration
# -----------------------------------------------------------------------------
#

class SegmentRegistration(ScriptedLoadableModule):
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Segment Registration"
    self.parent.categories = ["Registration"]
    self.parent.dependencies = ["SubjectHierarchy", "Segmentations", "CropVolume", "BRAINSFit", "DistanceMapBasedRegistration"]
    self.parent.contributors = ["Csaba Pinter (Queen's)"]
    self.parent.helpText = """
    Registration of segmented structures, and transformation of the whole segmentation (and its anatomical image) with the resulting transformation. Supports affine and deformable.
    """
    self.parent.acknowledgementText = """This file was originally developed by Csaba Pinter, PerkLab, Queen's University and was supported through the Applied Cancer Research Unit program of Cancer Care Ontario with funds provided by the Ontario Ministry of Health and Long-Term Care""" # replace with organization, grant and thanks.

#
# -----------------------------------------------------------------------------
# SegmentRegistration_Widget
# -----------------------------------------------------------------------------
#

class SegmentRegistrationWidget(ScriptedLoadableModuleWidget):

  #------------------------------------------------------------------------------
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Flag determining whether buttons for testing each step are visible
    self.testingButtonsVisible = False

    # Create logic
    self.logic = SegmentRegistrationLogic()
    slicer.segmentRegistrationLogic = self.logic # For debugging

    # Create collapsible button for inputs
    self.registrationCollapsibleButton = ctk.ctkCollapsibleButton()
    self.registrationCollapsibleButton.text = "Registration"
    self.registrationCollapsibleButtonLayout = qt.QFormLayout(self.registrationCollapsibleButton)

    # User interface

    # Fixed volume node combobox
    self.fixedVolumeNodeCombobox = slicer.qMRMLNodeComboBox()
    self.fixedVolumeNodeCombobox.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.fixedVolumeNodeCombobox.showChildNodeTypes = False
    self.fixedVolumeNodeCombobox.noneEnabled = False
    self.fixedVolumeNodeCombobox.setMRMLScene( slicer.mrmlScene )
    self.fixedVolumeNodeCombobox.setToolTip( "Select fixed image" )
    self.fixedVolumeNodeCombobox.name = "fixedVolumeNodeCombobox"
    self.registrationCollapsibleButtonLayout.addRow('Fixed image: ', self.fixedVolumeNodeCombobox)
    self.fixedVolumeNodeCombobox.connect('currentNodeChanged(vtkMRMLNode*)', self.onFixedVolumeNodeSelectionChanged)

    # Fixed segmentation node combobox
    self.fixedSegmentationNodeCombobox = slicer.qMRMLNodeComboBox()
    self.fixedSegmentationNodeCombobox.nodeTypes = ( ("vtkMRMLSegmentationNode"), "" )
    self.fixedSegmentationNodeCombobox.noneEnabled = False
    self.fixedSegmentationNodeCombobox.setMRMLScene( slicer.mrmlScene )
    self.fixedSegmentationNodeCombobox.setToolTip( "Select fixed segmentation" )
    self.fixedSegmentationNodeCombobox.name = "fixedSegmentationNodeCombobox"
    self.registrationCollapsibleButtonLayout.addRow('Fixed segmentation: ', self.fixedSegmentationNodeCombobox)
    self.fixedSegmentationNodeCombobox.connect('currentNodeChanged(vtkMRMLNode*)', self.onFixedSegmentationNodeSelectionChanged)

    # Fixed segment name combobox
    self.fixedSegmentNameCombobox = qt.QComboBox()
    self.registrationCollapsibleButtonLayout.addRow('Fixed segment: ', self.fixedSegmentNameCombobox)
    self.fixedSegmentNameCombobox.connect('currentIndexChanged(QString)', self.onFixedSegmentSelectionChanged)
    self.fixedSegmentNameCombobox.enabled = False

    # Moving volume node combobox
    self.movingVolumeNodeCombobox = slicer.qMRMLNodeComboBox()
    self.movingVolumeNodeCombobox.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.movingVolumeNodeCombobox.showChildNodeTypes = False
    self.movingVolumeNodeCombobox.noneEnabled = False
    self.movingVolumeNodeCombobox.setMRMLScene( slicer.mrmlScene )
    self.movingVolumeNodeCombobox.setToolTip( "Select moving image" )
    self.movingVolumeNodeCombobox.name = "movingVolumeNodeCombobox"
    self.registrationCollapsibleButtonLayout.addRow('Moving image: ', self.movingVolumeNodeCombobox)
    self.movingVolumeNodeCombobox.connect('currentNodeChanged(vtkMRMLNode*)', self.onMovingVolumeNodeSelectionChanged)

    # Moving segmentation node combobox
    self.movingSegmentationNodeCombobox = slicer.qMRMLNodeComboBox()
    self.movingSegmentationNodeCombobox.nodeTypes = ( ("vtkMRMLSegmentationNode"), "" )
    self.movingSegmentationNodeCombobox.noneEnabled = False
    self.movingSegmentationNodeCombobox.setMRMLScene( slicer.mrmlScene )
    self.movingSegmentationNodeCombobox.setToolTip( "Select moving segmentation" )
    self.movingSegmentationNodeCombobox.name = "movingSegmentationNodeCombobox"
    self.registrationCollapsibleButtonLayout.addRow('Moving segmentation: ', self.movingSegmentationNodeCombobox)
    self.movingSegmentationNodeCombobox.connect('currentNodeChanged(vtkMRMLNode*)', self.onMovingSegmentationNodeSelectionChanged)

    # Moving segment name combobox
    self.movingSegmentNameCombobox = qt.QComboBox()
    self.registrationCollapsibleButtonLayout.addRow('Moving segment: ', self.movingSegmentNameCombobox)
    self.movingSegmentNameCombobox.connect('currentIndexChanged(QString)', self.onMovingSegmentSelectionChanged)
    self.movingSegmentNameCombobox.enabled = False

    self.keepIntermediateNodesCheckBox = qt.QCheckBox()
    self.keepIntermediateNodesCheckBox.checked = self.logic.keepIntermediateNodes
    self.keepIntermediateNodesCheckBox.setToolTip('If checked, then data nodes created during processing are kept in the scene, removed otherwise.\nUseful to see details of the registration algorithm, but not for routine usage when only the result is of interest.')
    self.registrationCollapsibleButtonLayout.addRow('Keep intermediate nodes: ', self.keepIntermediateNodesCheckBox)
    self.keepIntermediateNodesCheckBox.connect('toggled(bool)', self.onKeepIntermediateNodesCheckBoxToggled)

    # Add empty row
    self.registrationCollapsibleButtonLayout.addRow(' ', None)

    # Perform registration button
    self.performRegistrationButton = qt.QPushButton("Perform registration")
    self.performRegistrationButton.toolTip = "Deformable registration between two structures, originally developed for contour propagation between modalities"
    self.performRegistrationButton.name = "performRegistrationButton"
    self.registrationCollapsibleButtonLayout.addRow(self.performRegistrationButton)
    self.performRegistrationButton.connect('clicked()', self.onPerformRegistration)

    # Buttons to perform parts of the workflow (for testing)
    if self.developerMode and self.testingButtonsVisible:
      # Add empty row
      self.registrationCollapsibleButtonLayout.addRow(' ', None)

      # Self test button
      self.selfTestButton = qt.QPushButton("Run self test")
      self.selfTestButton.setMaximumWidth(300)
      self.selfTestButton.name = "selfTestButton"
      self.registrationCollapsibleButtonLayout.addWidget(self.selfTestButton)
      self.selfTestButton.connect('clicked()', self.onSelfTest)

      # Crop moving button
      self.cropMovingVolumeButton = qt.QPushButton("Crop moving volume")
      self.cropMovingVolumeButton.setMaximumWidth(200)
      self.cropMovingVolumeButton.name = "cropMovingVolumeButton"
      self.registrationCollapsibleButtonLayout.addWidget(self.cropMovingVolumeButton)
      self.cropMovingVolumeButton.connect('clicked()', self.onCropMovingVolume)

      # Pre-align segmentations button
      self.preAlignSegmentationsButton = qt.QPushButton("Pre-align segmentations")
      self.preAlignSegmentationsButton.setMaximumWidth(200)
      self.preAlignSegmentationsButton.name = "preAlignSegmentationsButton"
      self.registrationCollapsibleButtonLayout.addWidget(self.preAlignSegmentationsButton)
      self.preAlignSegmentationsButton.connect('clicked()', self.onPreAlignSegmentations)

      # Resample fixed button
      self.resampleFixedButton = qt.QPushButton("Resample fixed volume")
      self.resampleFixedButton.setMaximumWidth(200)
      self.resampleFixedButton.name = "resampleFixedButton"
      self.registrationCollapsibleButtonLayout.addWidget(self.resampleFixedButton)
      self.resampleFixedButton.connect('clicked()', self.onResampleFixedVolume)

      # Create contour labelmaps
      self.createContourLabelmapsButton = qt.QPushButton("Create contour labelmaps")
      self.createContourLabelmapsButton.setMaximumWidth(200)
      self.createContourLabelmapsButton.toolTip = ""
      self.createContourLabelmapsButton.name = "createContourLabelmapsButton"
      self.registrationCollapsibleButtonLayout.addWidget(self.createContourLabelmapsButton)
      self.createContourLabelmapsButton.connect('clicked()', self.onCreateContourLabelmaps)

      # Perform distance based registration button
      self.performDistanceBasedRegistrationButton = qt.QPushButton("Perform distance based registration")
      self.performDistanceBasedRegistrationButton.setMaximumWidth(200)
      self.performDistanceBasedRegistrationButton.name = "performDistanceBasedRegistrationButton"
      self.registrationCollapsibleButtonLayout.addWidget(self.performDistanceBasedRegistrationButton)
      self.performDistanceBasedRegistrationButton.connect('clicked()', self.onPerformDistanceBasedRegistration)

    self.layout.addWidget(self.registrationCollapsibleButton)

    # Collapsible button for results
    self.resultsCollapsibleButton = ctk.ctkCollapsibleButton()
    self.resultsCollapsibleButton.text = "Results"
    self.resultsCollapsibleButton.enabled = False
    self.resultsCollapsibleButtonLayout = qt.QVBoxLayout(self.resultsCollapsibleButton)

    # Transformation radio buttons
    self.transformationLayout = qt.QHBoxLayout()
    self.noRegistrationRadioButton = qt.QRadioButton('None')
    self.rigidRegistrationRadioButton = qt.QRadioButton('Rigid')
    self.deformableRegistrationRadioButton = qt.QRadioButton('Deformable')
    self.deformableRegistrationRadioButton.checked = True
    self.noRegistrationRadioButton.connect('clicked()', self.onTransformationModeChanged)
    self.rigidRegistrationRadioButton.connect('clicked()', self.onTransformationModeChanged)
    self.deformableRegistrationRadioButton.connect('clicked()', self.onTransformationModeChanged)
    self.transformationLayout.addWidget(qt.QLabel('Applied registration on moving study: '))
    self.transformationLayout.addWidget(self.noRegistrationRadioButton)
    self.transformationLayout.addWidget(self.rigidRegistrationRadioButton)
    self.transformationLayout.addWidget(self.deformableRegistrationRadioButton)
    self.resultsCollapsibleButtonLayout.addLayout(self.transformationLayout)

    self.layout.addWidget(self.resultsCollapsibleButton)

    # Add vertical spacer
    self.layout.addStretch(4)

  #------------------------------------------------------------------------------
  def enter(self):
    # Runs whenever the module is reopened
    self.onFixedVolumeNodeSelectionChanged(self.fixedVolumeNodeCombobox.currentNode())
    self.onFixedSegmentationNodeSelectionChanged(self.fixedSegmentationNodeCombobox.currentNode())
    self.onMovingVolumeNodeSelectionChanged(self.movingVolumeNodeCombobox.currentNode())
    self.onMovingSegmentationNodeSelectionChanged(self.movingSegmentationNodeCombobox.currentNode())

  #------------------------------------------------------------------------------
  def exit(self):
    pass

  #------------------------------------------------------------------------------
  def onDicomLoad(self):
    slicer.modules.dicom.widgetRepresentation()
    slicer.modules.DICOMWidget.enter()

  #------------------------------------------------------------------------------
  def onFixedVolumeNodeSelectionChanged(self, fixedVolumeNode):
    self.logic.fixedVolumeNode = fixedVolumeNode

  #------------------------------------------------------------------------------
  def onFixedSegmentationNodeSelectionChanged(self, fixedSegmentationNode):
    self.logic.fixedSegmentationNode = fixedSegmentationNode
    self.populateSegmentCombobox(self.logic.fixedSegmentationNode, self.fixedSegmentNameCombobox)

  #------------------------------------------------------------------------------
  def onFixedSegmentSelectionChanged(self, fixedSegmentName):
    self.logic.fixedSegmentName = fixedSegmentName

  #------------------------------------------------------------------------------
  def onMovingVolumeNodeSelectionChanged(self, movingVolumeNode):
    self.logic.movingVolumeNode = movingVolumeNode

  #------------------------------------------------------------------------------
  def onMovingSegmentationNodeSelectionChanged(self, movingSegmentationNode):
    self.logic.movingSegmentationNode = movingSegmentationNode
    self.populateSegmentCombobox(self.logic.movingSegmentationNode, self.movingSegmentNameCombobox)

  #------------------------------------------------------------------------------
  def onMovingSegmentSelectionChanged(self, movingSegmentName):
    self.logic.movingSegmentName = movingSegmentName

  #------------------------------------------------------------------------------
  def onKeepIntermediateNodesCheckBoxToggled(self, checked):
    self.logic.keepIntermediateNodes = checked

  #------------------------------------------------------------------------------
  def onPerformRegistration(self):
    if self.logic.performRegistration():
      self.onRegistrationSuccessful()

  #------------------------------------------------------------------------------
  def onCropMovingVolume(self):
    self.logic.cropMovingVolume()

  #------------------------------------------------------------------------------
  def onPreAlignSegmentations(self):
    self.logic.preAlignSegmentations()

  #------------------------------------------------------------------------------
  def onResampleFixedVolume(self):
    self.logic.resampleFixedVolume()

  #------------------------------------------------------------------------------
  def onCreateContourLabelmaps(self):
    self.logic.createContourLabelmaps()

  #------------------------------------------------------------------------------
  def onPerformDistanceBasedRegistration(self):
    if self.logic.performDistanceBasedRegistration():
      self.onRegistrationSuccessful()

  #------------------------------------------------------------------------------
  def onRegistrationSuccessful(self):
    # Enable results section
    self.resultsCollapsibleButton.enabled = True

    # Show deformed results
    self.deformableRegistrationRadioButton.checked = True
    self.logic.applyDeformableTransformation()

    # Setup better visualization of the results
    self.logic.setupResultVisualization()

  #------------------------------------------------------------------------------
  def onTransformationModeChanged(self):
    if self.noRegistrationRadioButton.checked:
      self.logic.applyNoTransformation()
    elif self.rigidRegistrationRadioButton.checked:
      self.logic.applyRigidTransformation()
    elif self.deformableRegistrationRadioButton.checked:
      self.logic.applyDeformableTransformation()

  #------------------------------------------------------------------------------
  def onSelfTest(self):
    slicer.mrmlScene.Clear(0)
    tester = SegmentRegistrationTest()
    tester.widget = self
    tester.test_SegmentRegistration_FullTest()

  #------------------------------------------------------------------------------
  #------------------------------------------------------------------------------
  def populateSegmentCombobox(self, segmentationNode, segmentNameCombobox):
    validSegmentation = segmentationNode is not None and segmentationNode.GetSegmentation().GetNumberOfSegments() > 0
    segmentNameCombobox.clear()
    segmentNameCombobox.enabled = validSegmentation
    if not validSegmentation:
      return

    segmentIDs = vtk.vtkStringArray()
    segmentationNode.GetSegmentation().GetSegmentIDs(segmentIDs)
    for segmentIndex in xrange(0,segmentIDs.GetNumberOfValues()):
      segmentID = segmentIDs.GetValue(segmentIndex)
      segment = segmentationNode.GetSegmentation().GetSegment(segmentID)
      segmentNameCombobox.addItem(segment.GetName(),segmentID)

#
# -----------------------------------------------------------------------------
# SegmentRegistrationLogic
# -----------------------------------------------------------------------------
#

class SegmentRegistrationLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """

  def __init__(self):
    self.fixedSegmentName = None
    self.fixedVolumeNode = None
    self.fixedSegmentationNode = None
    self.fixedResampledVolumeNode = None
    self.fixedLabelmap = None

    self.movingSegmentName = None
    self.movingVolumeNode = None
    self.movingSegmentationNode = None
    self.movingCroppedVolumeNode = None
    self.movingLabelmap = None
    self.movingVolumeNodeForExport = None
    self.movingSegmentationNodeForExport = None

    self.affineTransformNode = None
    self.bsplineTransformNode = None

    # Flag determining whether to keep temporary intermediate nodes in the scene
    # such as ROI, models, distance maps, smoothed volumes
    self.keepIntermediateNodes = False

  #------------------------------------------------------------------------------
  def performRegistration(self):
    logging.info('Performing registration workflow')
    self.cropMovingVolume()
    self.preAlignSegmentations()
    self.resampleFixedVolume()
    self.createContourLabelmaps()
    return self.performDistanceBasedRegistration()

  #------------------------------------------------------------------------------
  def cropMovingVolume(self):
    logging.info('Cropping moving volume')
    if not self.movingVolumeNode or not self.movingSegmentationNode:
      logging.error('Unable to access MR volume or segmentation')
      return

    # Create ROI
    roiNode = slicer.vtkMRMLAnnotationROINode()
    roiNode.SetName('CropROI_' + self.movingVolumeNode.GetName())
    slicer.mrmlScene.AddNode(roiNode)

    # Determine ROI position
    bounds = [0]*6
    self.movingSegmentationNode.GetSegmentation().GetBounds(bounds)
    center = [(bounds[0]+bounds[1])/2, (bounds[2]+bounds[3])/2, (bounds[4]+bounds[5])/2]
    roiNode.SetXYZ(center[0], center[1], center[2])

    # Determine ROI size (add structure width along RL axis, square slice, add height/2 along IS)
    #TODO: Support tilted volumes
    structureLR3 = (bounds[1]-bounds[0]) * 3
    structureIS2 = (bounds[5]-bounds[4]) * 2
    radius = [structureLR3/2, structureLR3/2, structureIS2/2]
    roiNode.SetRadiusXYZ(radius[0], radius[1], radius[2])

    # Crop moving volume
    cropParams = slicer.vtkMRMLCropVolumeParametersNode()
    cropParams.SetInputVolumeNodeID(self.movingVolumeNode.GetID())
    cropParams.SetROINodeID(roiNode.GetID())
    cropParams.SetVoxelBased(True)
    slicer.mrmlScene.AddNode(cropParams)
    cropLogic = slicer.modules.cropvolume.logic()
    cropLogic.Apply(cropParams)

    # Add resampled moving volume and cropping ROI to the same study as the original moving
    self.movingCroppedVolumeNode = cropParams.GetOutputVolumeNode()
    if self.movingCroppedVolumeNode is None:
      logging.error('Unable to access cropped moving volume')
      return
    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    movingStudyItemID = shNode.GetItemParent(shNode.GetItemByDataNode(self.movingVolumeNode))
    croppedMovingVolumeShItemID = shNode.GetItemByDataNode(self.movingCroppedVolumeNode)
    if movingStudyItemID:
      shNode.SetItemParent(croppedMovingVolumeShItemID, movingStudyItemID)

    if not self.keepIntermediateNodes:
      slicer.mrmlScene.RemoveNode(roiNode)
    else:
      roiShItemID = shNode.GetItemByDataNode(roiNode)
      if not roiShItemID:
        logging.error('Unable to access crop ROI subject hierarchy item')
        return
      shNode.SetItemParent(roiShItemID, movingStudyItemID)

      # Hide ROI by default
      shNode.SetDisplayVisibilityForBranch(roiShItemID, 0)

  #------------------------------------------------------------------------------
  def preAlignSegmentations(self):
    logging.info('Pre-aligning segmentations')
    if self.movingSegmentationNode is None or self.movingVolumeNode is None or self.movingCroppedVolumeNode is None or self.fixedSegmentationNode is None:
      logging.error('Invalid data selection')
      return
    # Get center of segmentation bounding boxes
    fixedBounds = [0]*6
    fixedSegment = self.fixedSegmentationNode.GetSegmentation().GetSegment(self.fixedSegmentName)
    if fixedSegment is None:
      logging.error('Failed to get fixed segment')
      return
    fixedSegment.GetBounds(fixedBounds)
    fixedCenter = [(fixedBounds[1]+fixedBounds[0])/2, (fixedBounds[3]+fixedBounds[2])/2, (fixedBounds[5]+fixedBounds[4])/2]
    logging.info('Fixed segment bounds: ' + repr(fixedBounds))
    movingBounds = [0]*6
    movingSegment = self.movingSegmentationNode.GetSegmentation().GetSegment(self.movingSegmentName)
    if movingSegment is None:
      logging.error('Failed to get moving segment')
      return
    movingSegment.GetBounds(movingBounds)
    movingCenter = [(movingBounds[1]+movingBounds[0])/2, (movingBounds[3]+movingBounds[2])/2, (movingBounds[5]+movingBounds[4])/2]
    logging.info('Moving segment bounds: ' + repr(movingBounds))

    # Create alignment transform
    moving2FixedTranslation = [fixedCenter[0]-movingCenter[0], fixedCenter[1]-movingCenter[1], fixedCenter[2]-movingCenter[2]]
    logging.info('Moving to fixed segment translation: ' + repr(moving2FixedTranslation))
    self.preAlignmentMoving2FixedLinearTransform = slicer.vtkMRMLLinearTransformNode()
    self.preAlignmentMoving2FixedLinearTransform.SetName(slicer.mrmlScene.GenerateUniqueName('PreAlignmentMoving2FixedLinearTransform'))
    slicer.mrmlScene.AddNode(self.preAlignmentMoving2FixedLinearTransform)
    moving2FixedMatrix = vtk.vtkMatrix4x4()
    moving2FixedMatrix.SetElement(0,3,moving2FixedTranslation[0])
    moving2FixedMatrix.SetElement(1,3,moving2FixedTranslation[1])
    moving2FixedMatrix.SetElement(2,3,moving2FixedTranslation[2])
    self.preAlignmentMoving2FixedLinearTransform.SetAndObserveMatrixTransformToParent(moving2FixedMatrix)

    #TODO: This snippet shows both ROIs for testing purposes
    # roi1Node = slicer.vtkMRMLAnnotationROINode()
    # roi1Node.SetName(slicer.mrmlScene.GenerateUniqueName('fixedBounds'))
    # slicer.mrmlScene.AddNode(roi1Node)
    # roi1Node.SetXYZ(fixedCenter[0], fixedCenter[1], fixedCenter[2])
    # roi1Node.SetRadiusXYZ((fixedBounds[1]-fixedBounds[0])/2, (fixedBounds[3]-fixedBounds[2])/2, (fixedBounds[5]-fixedBounds[4])/2)
    # roi2Node = slicer.vtkMRMLAnnotationROINode()
    # roi2Node.SetName(slicer.mrmlScene.GenerateUniqueName('movingBounds'))
    # slicer.mrmlScene.AddNode(roi2Node)
    # roi2Node.SetXYZ(movingCenter[0], movingCenter[1], movingCenter[2])
    # roi2Node.SetRadiusXYZ((movingBounds[1]-movingBounds[0])/2, (movingBounds[3]-movingBounds[2])/2, (movingBounds[5]-movingBounds[4])/2)
    # return

    # Apply transform to fixed image and segmentation
    self.movingVolumeNode.SetAndObserveTransformNodeID(self.preAlignmentMoving2FixedLinearTransform.GetID())
    self.movingSegmentationNode.SetAndObserveTransformNodeID(self.preAlignmentMoving2FixedLinearTransform.GetID())
    self.movingCroppedVolumeNode.SetAndObserveTransformNodeID(self.preAlignmentMoving2FixedLinearTransform.GetID())

    # Harden transform
    slicer.vtkSlicerTransformLogic.hardenTransform(self.movingVolumeNode)
    slicer.vtkSlicerTransformLogic.hardenTransform(self.movingSegmentationNode)
    slicer.vtkSlicerTransformLogic.hardenTransform(self.movingCroppedVolumeNode)

  #------------------------------------------------------------------------------
  def resampleFixedVolume(self):
    logging.info('Resampling fixed volume')
    if not self.fixedVolumeNode:
      logging.error('Unable to access fixed volume')
      return

    # Create putput volume
    self.fixedResampledVolumeNode = slicer.vtkMRMLScalarVolumeNode()
    self.fixedResampledVolumeNode.SetName(self.fixedVolumeNode.GetName() + '_Resampled_1x1x1mm')
    slicer.mrmlScene.AddNode(self.fixedResampledVolumeNode)

    # Resample
    resampleParameters = {'outputPixelSpacing':'1,1,1', 'interpolationType':'lanczos', 'InputVolume':self.fixedVolumeNode.GetID(), 'OutputVolume':self.fixedResampledVolumeNode.GetID()}
    slicer.cli.run(slicer.modules.resamplescalarvolume, None, resampleParameters, wait_for_completion=True)

    # Add resampled fixed volume to the same study as the original fixed volume
    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    fixedStudyItemID = shNode.GetItemParent(shNode.GetItemByDataNode(self.fixedVolumeNode))
    resampledFixedVolumeShItemID = shNode.GetItemByDataNode(self.fixedResampledVolumeNode)
    if not resampledFixedVolumeShItemID:
      logging.error('Unable to access resampled US subject hierarchy item')
      return
    shNode.SetItemParent(resampledFixedVolumeShItemID, fixedStudyItemID)

  #------------------------------------------------------------------------------
  def createContourLabelmaps(self):
    logging.info('Creating contour labelmaps')
    if self.movingSegmentationNode is None or self.fixedSegmentationNode is None:
      logging.error('Unable to access segmentations')
    
    # Make sure the segmentations have the labelmaps
    self.movingSegmentationNode.GetSegmentation().CreateRepresentation(slicer.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName())
    self.fixedSegmentationNode.GetSegmentation().CreateRepresentation(slicer.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName())
    # Get labelmap oriented image data
    movingOrientedImageData = slicer.vtkOrientedImageData()
    movingOrientedImageData.DeepCopy(self.movingSegmentationNode.GetSegmentation().GetSegment(self.movingSegmentName).GetRepresentation(slicer.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName()))
    fixedOrientedImageData = slicer.vtkOrientedImageData()
    fixedOrientedImageData.DeepCopy(self.fixedSegmentationNode.GetSegmentation().GetSegment(self.fixedSegmentName).GetRepresentation(slicer.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName()))

    # Get moving anatomy volume geometry
    movingAnatomyOrientedImageData = slicer.vtkSlicerSegmentationsModuleLogic.CreateOrientedImageDataFromVolumeNode(self.movingCroppedVolumeNode)
    movingAnatomyOrientedImageData.UnRegister(None)

    # Ensure same geometry of oriented image data
    if not slicer.vtkOrientedImageDataResample.DoGeometriesMatch(movingOrientedImageData, movingAnatomyOrientedImageData):
      slicer.vtkOrientedImageDataResample.ResampleOrientedImageToReferenceOrientedImage(movingOrientedImageData, movingAnatomyOrientedImageData, movingOrientedImageData, True, True)
    if not slicer.vtkOrientedImageDataResample.DoGeometriesMatch(fixedOrientedImageData, movingAnatomyOrientedImageData):
      slicer.vtkOrientedImageDataResample.ResampleOrientedImageToReferenceOrientedImage(fixedOrientedImageData, movingAnatomyOrientedImageData, fixedOrientedImageData, True, True)

    # Export segment binary labelmaps to labelmap nodes
    self.fixedLabelmap = slicer.vtkMRMLLabelMapVolumeNode()
    self.fixedLabelmap.SetName(slicer.mrmlScene.GenerateUniqueName('Fixed_Structure_Padded'))
    slicer.mrmlScene.AddNode(self.fixedLabelmap)
    self.fixedLabelmap.CreateDefaultDisplayNodes()

    self.movingLabelmap = slicer.vtkMRMLLabelMapVolumeNode()
    self.movingLabelmap.SetName(slicer.mrmlScene.GenerateUniqueName('Moving_Structure_Padded'))
    slicer.mrmlScene.AddNode(self.movingLabelmap)
    self.movingLabelmap.CreateDefaultDisplayNodes()

    ret1 = slicer.vtkSlicerSegmentationsModuleLogic.CreateLabelmapVolumeFromOrientedImageData(fixedOrientedImageData, self.fixedLabelmap)
    ret2 = slicer.vtkSlicerSegmentationsModuleLogic.CreateLabelmapVolumeFromOrientedImageData(movingOrientedImageData, self.movingLabelmap)
    if ret1 is False or ret2 is False:
      logging.error('Failed to create labelmap nodes')

    # Add labelmaps to the corresponding studies in subject hierarchy
    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    fixedStudyItemID = shNode.GetItemParent(shNode.GetItemByDataNode(self.fixedVolumeNode))
    movingStudyItemID = shNode.GetItemParent(shNode.GetItemByDataNode(self.movingVolumeNode))
    fixedLabelmapShItemID = shNode.GetItemByDataNode(self.fixedLabelmap)
    movingLabelmapShItemID = shNode.GetItemByDataNode(self.movingLabelmap)
    if fixedLabelmapShItemID and self.movingLabelmap:
      shNode.SetItemParent(movingLabelmapShItemID, fixedStudyItemID)
      shNode.SetItemParent(fixedLabelmapShItemID, movingStudyItemID)

  #------------------------------------------------------------------------------
  def performDistanceBasedRegistration(self):
    logging.info('Performing distance based registration')

    # Register using Distance Map Based Registration
    slicer.modules.distancemapbasedregistration.createNewWidgetRepresentation()
    distMapRegModuleWidget = slicer.modules.DistanceMapBasedRegistrationWidget
    distMapRegModuleWidget.fixedImageSelector.setCurrentNode(self.fixedVolumeNode)
    distMapRegModuleWidget.fixedImageLabelSelector.setCurrentNode(self.fixedLabelmap)
    distMapRegModuleWidget.movingImageSelector.setCurrentNode(self.movingVolumeNode)
    distMapRegModuleWidget.movingImageLabelSelector.setCurrentNode(self.movingLabelmap)
    self.affineTransformNode = distMapRegModuleWidget.affineTransformSelector.addNode()
    self.bsplineTransformNode = distMapRegModuleWidget.bsplineTransformSelector.addNode()
    success = True
    try:
      distMapRegModuleWidget.applyButton.click()
    except:
      success = False
      logging.error('Distance map based registration failed')
      return

    if not self.keepIntermediateNodes:
      qt.QTimer.singleShot(250, self.removeIntermedateNodes) # Otherwise Slicer crashes
    else:
      # Move nodes created by the distance map based registration ot the proper subject hierarchy branches
      pass #TODO

    return success

  #------------------------------------------------------------------------------
  def removeIntermedateNodes(self):
    # Remove nodes created during preprocessing for the distance based registration
    slicer.mrmlScene.RemoveNode(self.fixedResampledVolumeNode)
    slicer.mrmlScene.RemoveNode(self.fixedLabelmap)
    slicer.mrmlScene.RemoveNode(self.movingLabelmap)

    # Remove nodes created by distance based registration
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('Fixed_Structure_Padded-Cropped'))
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('Fixed_Structure_Padded-Smoothed'))
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('Fixed_Structure_Padded-DistanceMap'))
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('Fixed_Structure_Padded-surface'))
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('Moving_Structure_Padded-Cropped'))
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('Moving_Structure_Padded-Smoothed'))
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('Moving_Structure_Padded-DistanceMap'))
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('Moving_Structure_Padded-surface'))
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('MovingImageCopy'))

  #------------------------------------------------------------------------------
  def applyNoTransformation(self):
    if self.movingVolumeNode is None or self.movingSegmentationNode is None:
      logging.error('Failed to apply transformation on moving volume and segmentation')
    # Apply transform on moving volume and segmentation
    self.movingVolumeNode.SetAndObserveTransformNodeID(None)
    self.movingSegmentationNode.SetAndObserveTransformNodeID(None)

  #------------------------------------------------------------------------------
  def applyRigidTransformation(self):
    if self.movingVolumeNode is None or self.movingSegmentationNode is None:
      logging.error('Failed to apply transformation on moving volume and segmentation')
    # Apply transform on moving volume and segmentation
    self.movingVolumeNode.SetAndObserveTransformNodeID(self.affineTransformNode.GetID())
    self.movingSegmentationNode.SetAndObserveTransformNodeID(self.affineTransformNode.GetID())

  #------------------------------------------------------------------------------
  def applyDeformableTransformation(self):
    if self.movingVolumeNode is None or self.movingSegmentationNode is None:
      logging.error('Failed to apply transformation on moving volume and segmentation')
    # Apply transform on moving volume and segmentation
    self.movingVolumeNode.SetAndObserveTransformNodeID(self.bsplineTransformNode.GetID())
    self.movingSegmentationNode.SetAndObserveTransformNodeID(self.bsplineTransformNode.GetID())

  #------------------------------------------------------------------------------
  def setupResultVisualization(self):
    logging.info('Setting up result visualization')
    if self.fixedSegmentationNode is None or self.movingSegmentationNode is None:
      logging.error('Failed to get segmentations')
    import vtkSegmentationCorePython as vtkSegmentationCore
    fixedSegment = self.fixedSegmentationNode.GetSegmentation().GetSegment(self.fixedSegmentName)
    movingSegment = self.movingSegmentationNode.GetSegmentation().GetSegment(self.movingSegmentName)
    if fixedSegment is None or movingSegment is None:
      logging.error('Failed to get segments')
      return

    # Make fixed segment red with 50% opacity
    fixedSegment.SetColor(1.0,0.0,0.0)
    fixedSegmentationDisplayNode = self.fixedSegmentationNode.GetDisplayNode()
    if fixedSegmentationDisplayNode is None:
      logging.error('Failed to get fixed segmentation display node')
      return
    fixedSegmentationDisplayNode.SetSegmentOpacity(self.fixedSegmentName, 0.5)

    # Make moving segment light blue with 50% opacity
    movingSegment.SetColor(0.43,0.72,0.82)
    movingSegmentationDisplayNode = self.movingSegmentationNode.GetDisplayNode()
    if movingSegmentationDisplayNode is None:
      logging.error('Failed to get moving segmentation display node')
      return
    movingSegmentationDisplayNode.SetSegmentOpacity(self.movingSegmentName, 0.5)


#
# -----------------------------------------------------------------------------
# SegmentRegistrationTest
# -----------------------------------------------------------------------------
#

class SegmentRegistrationTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  """

  #------------------------------------------------------------------------------
  def test_SegmentRegistration_FullTest(self):
    try:
      # Check for modules
      self.assertIsNotNone( slicer.modules.dicomrtimportexport ) # The test uses RT but the module itself does not
      self.assertIsNotNone( slicer.modules.subjecthierarchy )
      self.assertIsNotNone( slicer.modules.segmentations )
      self.assertIsNotNone( slicer.modules.brainsfit )
      self.assertIsNotNone( slicer.modules.distancemapbasedregistration )
      self.assertIsNotNone( slicer.modules.cropvolume )

      self.TestSection_00_SetupPathsAndNames()
      self.TestSection_01_LoadDicomData()
      self.TestSection_02_PerformRegistration()

    except Exception, e:
      logging.error('Exception happened! Details:')
      import traceback
      traceback.print_exc()

  #------------------------------------------------------------------------------
  def TestSection_00_SetupPathsAndNames(self):
    segmentRegistrationDir = slicer.app.temporaryPath + '/SegmentRegistration'
    if not os.access(segmentRegistrationDir, os.F_OK):
      os.mkdir(segmentRegistrationDir)

    self.dicomDataDir = segmentRegistrationDir + '/MRIUSFusionPatient4Dicom'
    if not os.access(self.dicomDataDir, os.F_OK):
      os.mkdir(self.dicomDataDir)

    self.dicomDatabaseDir = segmentRegistrationDir + '/CtkDicomDatabase'
    self.dicomZipFileUrl = 'http://slicer.kitware.com/midas3/download/item/318330/MRIUSFusionPatient4.zip'
    self.dicomZipFilePath = segmentRegistrationDir + '/MRIUSFusionPatient4.zip'
    self.expectedNumOfFilesInDicomDataDir = 251
    self.tempDir = segmentRegistrationDir + '/Temp'

    self.patientName = '0PHYSIQUE^F_MRI_US_4 (PHYEP004)'
    self.usSegmentationName = '1: RTSTRUCT: OCP RTS v4.2.21'
    self.usSegmentName = 'target'
    self.usVolumeName = '1: Oncentra Prostate Image Series'
    self.mrSegmentationName = '9: RTSTRUCT: Prostate'
    self.mrSegmentName = 'Prostate'
    self.mrVolumeName = '4: T2 SPACE RST TRA ISO 3D'

    self.setupPathsAndNamesDone = True

  #------------------------------------------------------------------------------
  def TestSection_01_LoadDicomData(self):
    try:
      # Open test database and empty it
      with DICOMUtils.TemporaryDICOMDatabase(self.dicomDatabaseDir) as db:
        self.assertTrue( db.isOpen )
        self.assertEqual( slicer.dicomDatabase, db)

        # Download, unzip, import, and load data. Verify selected plugins and loaded nodes.
        selectedPlugins = { 'Scalar Volume':2, 'RT':2 }
        loadedNodes = { 'vtkMRMLScalarVolumeNode':2, \
                        'vtkMRMLSegmentationNode':2 }
        with DICOMUtils.LoadDICOMFilesToDatabase( \
            self.dicomZipFileUrl, self.dicomZipFilePath, \
            self.dicomDataDir, self.expectedNumOfFilesInDicomDataDir, \
            {}, loadedNodes) as success:
          self.assertTrue(success)

    except Exception, e:
      import traceback
      traceback.print_exc()
      self.delayDisplay('Test caused exception!\n' + str(e),self.delayMs*2)
      raise Exception("Exception occurred, handled, thrown further to workflow level")

  #------------------------------------------------------------------------------
  def TestSection_02_PerformRegistration(self):
    self.delayDisplay("Perform registration",self.delayMs)

    # Check patient item
    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    patientShItemID = shNode.GetItemChildWithName(shNode.GetSceneItemID(), self.patientName)
    self.assertNotEqual(patientShItemID, 0)

    try:
      slicer.util.selectModule('SegmentRegistration')
      moduleWidget = slicer.modules.segmentregistration.widgetRepresentation().self()

      # Make volume selections
      usVolumeNode = slicer.util.getNode(self.usVolumeName)
      self.assertIsNotNone(usVolumeNode)
      moduleWidget.fixedVolumeNodeCombobox.setCurrentNode(usVolumeNode)

      mrVolumeNode = slicer.util.getNode(self.mrVolumeName)
      self.assertIsNotNone(mrVolumeNode)
      moduleWidget.movingVolumeNodeCombobox.setCurrentNode(mrVolumeNode)

      # Set fixed segmentation and segment
      usSegmentationNode = slicer.util.getNode(self.usSegmentationName)
      self.assertIsNotNone(usSegmentationNode)
      moduleWidget.fixedSegmentationNodeCombobox.setCurrentNode(usSegmentationNode)
      moduleWidget.fixedSegmentNameCombobox.setCurrentIndex(
        moduleWidget.fixedSegmentNameCombobox.findText(self.usSegmentName) )
      self.assertEqual(moduleWidget.fixedSegmentNameCombobox.currentText, self.usSegmentName)

      # Set moving segmentation and segment
      mrSegmentationNode = slicer.util.getNode(self.mrSegmentationName)
      self.assertIsNotNone(mrSegmentationNode)
      moduleWidget.movingSegmentationNodeCombobox.setCurrentNode(mrSegmentationNode)
      moduleWidget.movingSegmentNameCombobox.setCurrentIndex(
        moduleWidget.movingSegmentNameCombobox.findText(self.mrSegmentName) )
      self.assertEqual(moduleWidget.movingSegmentNameCombobox.currentText, self.mrSegmentName)

      # Perform registration
      qt.QApplication.setOverrideCursor(qt.QCursor(qt.Qt.BusyCursor))
      success = moduleWidget.logic.performRegistration()
      qt.QApplication.restoreOverrideCursor()
      self.assertTrue(success)

      # Check transforms
      preAlignmentTransformNode = slicer.util.getNode('PreAlignmentMoving2FixedLinearTransform')
      self.assertIsNotNone(preAlignmentTransformNode)
      affineTransformNode = slicer.util.getNode('Affine Transform')
      self.assertIsNotNone(affineTransformNode)
      deformableTransformNode = slicer.util.getNode('Deformable Transform')
      self.assertIsNotNone(deformableTransformNode)

      # Set transforms and visualization
      moduleWidget.onRegistrationSuccessful()
      self.delayDisplay("Waiting for UI updates",self.delayMs*2)
      self.assertIsNotNone(mrSegmentationNode.GetParentTransformNode())
      mrVolumeNode = slicer.util.getNode(self.mrVolumeName)
      self.assertIsNotNone(mrVolumeNode)
      self.assertIsNotNone(mrVolumeNode.GetParentTransformNode())

    except Exception, e:
      import traceback
      traceback.print_exc()
      self.delayDisplay('Test caused exception!\n' + str(e),self.delayMs*2)
      raise Exception("Exception occurred, handled, thrown further to workflow level")

  #------------------------------------------------------------------------------
  # Mandatory functions
  #------------------------------------------------------------------------------
  def setUp(self, clearScene=True):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    if clearScene:
      slicer.mrmlScene.Clear(0)

    self.delayMs = 700

    self.moduleName = "SegmentRegistration"

  #------------------------------------------------------------------------------
  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()

    self.test_SegmentRegistration_FullTest()
