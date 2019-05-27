import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

invalidShItemID = slicer.vtkMRMLSubjectHierarchyNode.GetInvalidItemID()

# -----------------------------------------------------------------------------
# Snippets for testing/debugging
# - Access logic
# pl = slicer.modules.prostatemriuscontourpropagation.widgetRepresentation().self().logic

#
# -----------------------------------------------------------------------------
# ProstateMRIUSContourPropagation
# -----------------------------------------------------------------------------
#

class ProstateMRIUSContourPropagation(ScriptedLoadableModule):
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Prostate MRI-US Contour Propagation"
    self.parent.categories = ["Radiotherapy"]
    self.parent.dependencies = ["DicomRtImportExport", "SubjectHierarchy", "Segmentations", "CropVolume", "BRAINSFit", "DistanceMapBasedRegistration", "SegmentComparison"]
    self.parent.contributors = ["Csaba Pinter (Queen's)"]
    self.parent.helpText = """
    Contour propagation for prostate MRI scans to US images for brachytherapy tumor tracking
    """
    self.parent.acknowledgementText = """This file was originally developed by Csaba Pinter, PerkLab, Queen's University and was supported through the Applied Cancer Research Unit program of Cancer Care Ontario with funds provided by the Ontario Ministry of Health and Long-Term Care""" # replace with organization, grant and thanks.

#
# -----------------------------------------------------------------------------
# ProstateMRIUSContourPropagation_Widget
# -----------------------------------------------------------------------------
#

class ProstateMRIUSContourPropagationWidget(ScriptedLoadableModuleWidget):

  #------------------------------------------------------------------------------
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Flag determining whether buttons for testing each step are visible
    self.testingButtonsVisible = False

    # Create logic
    self.logic = ProstateMRIUSContourPropagationLogic()
    slicer.prostateMRIUSContourPropagationLogic = self.logic # For debugging

    # Create collapsible button for inputs
    self.registrationCollapsibleButton = ctk.ctkCollapsibleButton()
    self.registrationCollapsibleButton.text = "Registration"
    self.registrationCollapsibleButtonLayout = qt.QFormLayout(self.registrationCollapsibleButton)

    # User interface

    # Load DICOM data button
    self.showDicomBrowserButton = qt.QPushButton("Load DICOM data")
    self.showDicomBrowserButton.toolTip = "Load data (images, structures)"
    self.showDicomBrowserButton.name = "showDicomBrowserButton"
    self.registrationCollapsibleButtonLayout.addRow(self.showDicomBrowserButton)
    self.showDicomBrowserButton.connect('clicked()', self.onDicomLoad)

    # US patient item combobox
    self.usPatientItemCombobox = slicer.qMRMLSubjectHierarchyComboBox()
    self.usPatientItemCombobox.setLevelFilter(slicer.vtkMRMLSubjectHierarchyConstants.GetDICOMLevelPatient())
    self.usPatientItemCombobox.setMRMLScene( slicer.mrmlScene )
    self.usPatientItemCombobox.setToolTip( "Select US patient" )
    self.usPatientItemCombobox.name = "usPatientItemCombobox"
    self.registrationCollapsibleButtonLayout.addRow('US patient: ', self.usPatientItemCombobox)
    self.usPatientItemCombobox.connect('currentItemChanged(vtkIdType)', self.onUSPatientSelectionChanged)

    # US volume node combobox
    self.usVolumeNodeCombobox = slicer.qMRMLNodeComboBox()
    self.usVolumeNodeCombobox.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.usVolumeNodeCombobox.showChildNodeTypes = False
    self.usVolumeNodeCombobox.noneEnabled = True
    self.usVolumeNodeCombobox.noneDisplay = 'Automatic search failed - please select'
    self.usVolumeNodeCombobox.setMRMLScene( slicer.mrmlScene )
    self.usVolumeNodeCombobox.setToolTip( "Select US image" )
    self.usVolumeNodeCombobox.name = "usVolumeNodeCombobox"
    self.registrationCollapsibleButtonLayout.addRow('US image: ', self.usVolumeNodeCombobox)
    self.usVolumeNodeCombobox.connect('currentNodeChanged(vtkMRMLNode*)', self.onUSVolumeNodeSelectionChanged)

    # US segmentation node combobox
    self.usSegmentationNodeCombobox = slicer.qMRMLNodeComboBox()
    self.usSegmentationNodeCombobox.nodeTypes = ( ("vtkMRMLSegmentationNode"), "" )
    self.usSegmentationNodeCombobox.noneEnabled = True
    self.usSegmentationNodeCombobox.noneDisplay = 'Automatic search failed - please select'
    self.usSegmentationNodeCombobox.setMRMLScene( slicer.mrmlScene )
    self.usSegmentationNodeCombobox.setToolTip( "Select US segmentation" )
    self.usSegmentationNodeCombobox.name = "usSegmentationNodeCombobox"
    self.registrationCollapsibleButtonLayout.addRow('US segmentation: ', self.usSegmentationNodeCombobox)
    self.usSegmentationNodeCombobox.connect('currentNodeChanged(vtkMRMLNode*)', self.onUSSegmentationNodeSelectionChanged)

    # US prostate segment name combobox
    self.usProstateSegmentNameCombobox = qt.QComboBox()
    self.registrationCollapsibleButtonLayout.addRow('US prostate segment: ', self.usProstateSegmentNameCombobox)
    self.usProstateSegmentNameCombobox.connect('currentIndexChanged(QString)', self.onUSProstateSegmentSelectionChanged)
    self.usProstateSegmentNameCombobox.enabled = False

    # MRI patient item combobox
    self.mrPatientItemCombobox = slicer.qMRMLSubjectHierarchyComboBox()
    self.mrPatientItemCombobox.setLevelFilter(slicer.vtkMRMLSubjectHierarchyConstants.GetDICOMLevelPatient())
    self.mrPatientItemCombobox.setMRMLScene( slicer.mrmlScene )
    self.mrPatientItemCombobox.setToolTip( "Select US patient" )
    self.mrPatientItemCombobox.name = "mrPatientItemCombobox"
    self.registrationCollapsibleButtonLayout.addRow('MRI patient: ', self.mrPatientItemCombobox)
    self.mrPatientItemCombobox.connect('currentItemChanged(vtkIdType)', self.onMRPatientSelectionChanged)

    # MRI volume node combobox
    self.mrVolumeNodeCombobox = slicer.qMRMLNodeComboBox()
    self.mrVolumeNodeCombobox.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.mrVolumeNodeCombobox.showChildNodeTypes = False
    self.mrVolumeNodeCombobox.noneEnabled = True
    self.mrVolumeNodeCombobox.noneDisplay = 'Automatic search failed - please select'
    self.mrVolumeNodeCombobox.setMRMLScene( slicer.mrmlScene )
    self.mrVolumeNodeCombobox.setToolTip( "Select MR image" )
    self.mrVolumeNodeCombobox.name = "mrVolumeNodeCombobox"
    self.registrationCollapsibleButtonLayout.addRow('MRI image: ', self.mrVolumeNodeCombobox)
    self.mrVolumeNodeCombobox.connect('currentNodeChanged(vtkMRMLNode*)', self.onMRVolumeNodeSelectionChanged)

    # MRI segmentation node combobox
    self.mrSegmentationNodeCombobox = slicer.qMRMLNodeComboBox()
    self.mrSegmentationNodeCombobox.nodeTypes = ( ("vtkMRMLSegmentationNode"), "" )
    self.mrSegmentationNodeCombobox.noneEnabled = True
    self.mrSegmentationNodeCombobox.noneDisplay = 'Automatic search failed - please select'
    self.mrSegmentationNodeCombobox.setMRMLScene( slicer.mrmlScene )
    self.mrSegmentationNodeCombobox.setToolTip( "Select MRI segmentation" )
    self.mrSegmentationNodeCombobox.name = "mrSegmentationNodeCombobox"
    self.registrationCollapsibleButtonLayout.addRow('MRI segmentation: ', self.mrSegmentationNodeCombobox)
    self.mrSegmentationNodeCombobox.connect('currentNodeChanged(vtkMRMLNode*)', self.onMRSegmentationNodeSelectionChanged)

    # MRI prostate segment name combobox
    self.mrProstateSegmentNameCombobox = qt.QComboBox()
    self.registrationCollapsibleButtonLayout.addRow('MRI prostate segment: ', self.mrProstateSegmentNameCombobox)
    self.mrProstateSegmentNameCombobox.connect('currentIndexChanged(QString)', self.onMRProstateSegmentSelectionChanged)
    self.mrProstateSegmentNameCombobox.enabled = False

    self.keepIntermediateNodesCheckBox = qt.QCheckBox()
    self.keepIntermediateNodesCheckBox.checked = self.logic.keepIntermediateNodes
    self.keepIntermediateNodesCheckBox.setToolTip('If checked, then data nodes created during processing are kept in the scene, removed otherwise.\nUseful to see details of the registration algorithm, but not for routine usage when only the result is of interest.')
    self.registrationCollapsibleButtonLayout.addRow('Keep intermediate nodes: ', self.keepIntermediateNodesCheckBox)
    self.keepIntermediateNodesCheckBox.connect('toggled(bool)', self.onKeepIntermediateNodesCheckBoxToggled)

    # Add empty row
    self.registrationCollapsibleButtonLayout.addRow(' ', None)

    # Perform registration button
    self.performRegistrationButton = qt.QPushButton("Perform registration")
    self.performRegistrationButton.toolTip = "Prostate contour propagation from  MRI to US"
    self.performRegistrationButton.name = "performRegistrationButton"
    self.registrationCollapsibleButtonLayout.addRow(self.performRegistrationButton)
    self.performRegistrationButton.connect('clicked()', self.onPerformRegistration)

    # MR DICOM export button
    self.mrDicomExportButton = qt.QPushButton("Export deformed MRI study to DICOM")
    self.mrDicomExportButton.toolTip = "Initiate export of the deformed MRI study containing the image and structures into DICOM files on local storage"
    self.mrDicomExportButton.name = "mrDicomExportButton"
    self.mrDicomExportButton.enabled = False
    self.registrationCollapsibleButtonLayout.addRow(self.mrDicomExportButton)
    self.mrDicomExportButton.connect('clicked()', self.onMrDicomExport)

    # US DICOM export button
    self.usDicomExportButton = qt.QPushButton("Export US with deformed structures to DICOM")
    self.usDicomExportButton.toolTip = "Initiate export of the US study containing the image and the deformed structures into DICOM files on local storage"
    self.usDicomExportButton.name = "usDicomExportButton"
    self.usDicomExportButton.enabled = False
    self.registrationCollapsibleButtonLayout.addRow(self.usDicomExportButton)
    self.usDicomExportButton.connect('clicked()', self.onUsDicomExport)

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

      # Crop MRI button
      self.cropMRIButton = qt.QPushButton("Crop MRI volume")
      self.cropMRIButton.setMaximumWidth(200)
      self.cropMRIButton.name = "cropMRIButton"
      self.registrationCollapsibleButtonLayout.addWidget(self.cropMRIButton)
      self.cropMRIButton.connect('clicked()', self.onCropMRI)

      # Pre-align segmentations button
      self.preAlignSegmentationsButton = qt.QPushButton("Pre-align segmentations")
      self.preAlignSegmentationsButton.setMaximumWidth(200)
      self.preAlignSegmentationsButton.name = "preAlignSegmentationsButton"
      self.registrationCollapsibleButtonLayout.addWidget(self.preAlignSegmentationsButton)
      self.preAlignSegmentationsButton.connect('clicked()', self.onPreAlignSegmentations)

      # Resample US button
      self.resampleUSButton = qt.QPushButton("Resample US volume")
      self.resampleUSButton.setMaximumWidth(200)
      self.resampleUSButton.name = "resampleUSButton"
      self.registrationCollapsibleButtonLayout.addWidget(self.resampleUSButton)
      self.resampleUSButton.connect('clicked()', self.onResampleUS)

      # Create prostate contour labelmaps
      self.createProstateContourLabelmapsButton = qt.QPushButton("Create prostate contour labelmaps")
      self.createProstateContourLabelmapsButton.setMaximumWidth(200)
      self.createProstateContourLabelmapsButton.toolTip = ""
      self.createProstateContourLabelmapsButton.name = "createProstateContourLabelmapsButton"
      self.registrationCollapsibleButtonLayout.addWidget(self.createProstateContourLabelmapsButton)
      self.createProstateContourLabelmapsButton.connect('clicked()', self.onCreateProstateContourLabelmaps)

      # Perform distance based registration button
      self.performDistanceBasedRegistrationButton = qt.QPushButton("Perform distance based registration")
      self.performDistanceBasedRegistrationButton.setMaximumWidth(200)
      self.performDistanceBasedRegistrationButton.name = "performDistanceBasedRegistrationButton"
      self.registrationCollapsibleButtonLayout.addWidget(self.performDistanceBasedRegistrationButton)
      self.performDistanceBasedRegistrationButton.connect('clicked()', self.onPerformDistanceBasedRegistration)

    self.layout.addWidget(self.registrationCollapsibleButton)

    # Collapsible button for evaluation
    self.evaluationCollapsibleButton = ctk.ctkCollapsibleButton()
    self.evaluationCollapsibleButton.text = "Evaluation"
    self.evaluationCollapsibleButton.enabled = False
    self.evaluationCollapsibleButtonLayout = qt.QVBoxLayout(self.evaluationCollapsibleButton)

    # Transformation radio buttons
    self.transformationLayout = qt.QHBoxLayout()
    self.noRegistrationRadioButton = qt.QRadioButton('None')
    self.rigidRegistrationRadioButton = qt.QRadioButton('Rigid')
    self.deformableRegistrationRadioButton = qt.QRadioButton('Deformable')
    self.deformableRegistrationRadioButton.checked = True
    self.noRegistrationRadioButton.connect('clicked()', self.onTransformationModeChanged)
    self.rigidRegistrationRadioButton.connect('clicked()', self.onTransformationModeChanged)
    self.deformableRegistrationRadioButton.connect('clicked()', self.onTransformationModeChanged)
    self.transformationLayout.addWidget(qt.QLabel('Applied registration on MR study: '))
    self.transformationLayout.addWidget(self.noRegistrationRadioButton)
    self.transformationLayout.addWidget(self.rigidRegistrationRadioButton)
    self.transformationLayout.addWidget(self.deformableRegistrationRadioButton)
    self.evaluationCollapsibleButtonLayout.addLayout(self.transformationLayout)

    # Calculate segment similarity button
    self.similarityLayout = qt.QHBoxLayout()
    self.similarityLayout.addWidget(qt.QLabel('Calculate prostate similarity metrics:'))
    self.calculateSegmentSimilarityButton = qt.QPushButton("Calculate similarity")
    self.calculateSegmentSimilarityButton.name = "calculateSegmentSimilarityButton"
    self.similarityLayout.addWidget(self.calculateSegmentSimilarityButton)
    self.calculateSegmentSimilarityButton.connect('clicked()', self.onCalculateSegmentSimilarity)
    self.evaluationCollapsibleButtonLayout.addLayout(self.similarityLayout)

    self.evaluationCollapsibleButtonLayout.addWidget(qt.QLabel('Fiducial-based evaluation:'))

    # Markups widget for US
    self.usFiducialList = slicer.qSlicerSimpleMarkupsWidget()
    self.evaluationCollapsibleButtonLayout.addWidget(self.usFiducialList)
    self.usFiducialList.setMRMLScene(slicer.mrmlScene)

    # Markups widget for MRI
    self.mrFiducialList = slicer.qSlicerSimpleMarkupsWidget()
    self.evaluationCollapsibleButtonLayout.addWidget(self.mrFiducialList)
    self.mrFiducialList.setMRMLScene(slicer.mrmlScene)

    # Perform registration button
    self.calculateFiducialErrorsButton = qt.QPushButton("Calculate fiducial errors")
    self.calculateFiducialErrorsButton.toolTip = "Calculate fiducial 3D TREs and distances along each axis"
    self.calculateFiducialErrorsButton.name = "calculateFiducialErrorsButton"
    self.evaluationCollapsibleButtonLayout.addWidget(self.calculateFiducialErrorsButton)
    self.calculateFiducialErrorsButton.connect('clicked()', self.onCalculateFiducialErrors)

    self.layout.addWidget(self.evaluationCollapsibleButton)

    # Add vertical spacer
    self.layout.addStretch(4)

  #------------------------------------------------------------------------------
  def onDicomLoad(self):
    slicer.modules.dicom.widgetRepresentation()
    slicer.modules.DICOMWidget.enter()

  #------------------------------------------------------------------------------
  def onUSPatientSelectionChanged(self, usPatientShItemID):
    self.logic.usPatientShItemID = usPatientShItemID
    self.logic.parseUSPatient()
    # Select parsed nodes in the comboboxes
    self.usVolumeNodeCombobox.setCurrentNode(self.logic.usVolumeNode)
    self.onUSVolumeNodeSelectionChanged(self.logic.usVolumeNode)
    self.usSegmentationNodeCombobox.setCurrentNode(self.logic.usSegmentationNode)
    self.onUSSegmentationNodeSelectionChanged(self.logic.usSegmentationNode)

  #------------------------------------------------------------------------------
  def onUSVolumeNodeSelectionChanged(self, usVolumeNode):
    self.logic.usVolumeNode = usVolumeNode

  #------------------------------------------------------------------------------
  def onUSSegmentationNodeSelectionChanged(self, usSegmentationNode):
    self.logic.usSegmentationNode = usSegmentationNode
    self.populateProstateSegmentCombobox(self.logic.usSegmentationNode, self.usProstateSegmentNameCombobox)

  #------------------------------------------------------------------------------
  def onUSProstateSegmentSelectionChanged(self, usProstateSegmentName):
    self.logic.usProstateSegmentName = usProstateSegmentName

  #------------------------------------------------------------------------------
  def onMRPatientSelectionChanged(self, mrPatientShItemID):
    self.logic.mrPatientShItemID = mrPatientShItemID
    self.logic.parseMRPatient()
    # Select parsed nodes in the comboboxes
    self.mrVolumeNodeCombobox.setCurrentNode(self.logic.mrVolumeNode)
    self.onMRVolumeNodeSelectionChanged(self.logic.mrVolumeNode)
    self.mrSegmentationNodeCombobox.setCurrentNode(self.logic.mrSegmentationNode)
    self.onMRSegmentationNodeSelectionChanged(self.logic.mrSegmentationNode)

  #------------------------------------------------------------------------------
  def onMRVolumeNodeSelectionChanged(self, mrVolumeNode):
    self.logic.mrVolumeNode = mrVolumeNode

  #------------------------------------------------------------------------------
  def onMRSegmentationNodeSelectionChanged(self, mrSegmentationNode):
    self.logic.mrSegmentationNode = mrSegmentationNode
    self.populateProstateSegmentCombobox(self.logic.mrSegmentationNode, self.mrProstateSegmentNameCombobox)

  #------------------------------------------------------------------------------
  def onMRProstateSegmentSelectionChanged(self, mrProstateSegmentName):
    self.logic.mrProstateSegmentName = mrProstateSegmentName

  #------------------------------------------------------------------------------
  def onKeepIntermediateNodesCheckBoxToggled(self, checked):
    self.logic.keepIntermediateNodes = checked

  #------------------------------------------------------------------------------
  def onPerformRegistration(self):
    qt.QApplication.setOverrideCursor(qt.QCursor(qt.Qt.BusyCursor))

    if self.logic.performRegistration():
      self.onRegistrationSuccessful()

    qt.QApplication.restoreOverrideCursor()

  #------------------------------------------------------------------------------
  def onMrDicomExport(self):
    self.logic.exportDeformedMrStudyToDicom()

  #------------------------------------------------------------------------------
  def onUsDicomExport(self):
    self.logic.exportDeformedUsStudyToDicom()

  #------------------------------------------------------------------------------
  def onLoadData(self):
    self.logic.loadData()

  #------------------------------------------------------------------------------
  def onCropMRI(self):
    self.logic.cropMRI()

  #------------------------------------------------------------------------------
  def onPreAlignSegmentations(self):
    self.logic.preAlignSegmentations()

  #------------------------------------------------------------------------------
  def onResampleUS(self):
    self.logic.resampleUS()

  #------------------------------------------------------------------------------
  def onCreateProstateContourLabelmaps(self):
    self.logic.createProstateContourLabelmaps()

  #------------------------------------------------------------------------------
  def onPerformDistanceBasedRegistration(self):
    if self.logic.performDistanceBasedRegistration():
      self.onRegistrationSuccessful()

  #------------------------------------------------------------------------------
  def onRegistrationSuccessful(self):
    # Enable export button and evaluation section
    self.mrDicomExportButton.enabled = True
    self.usDicomExportButton.enabled = True
    self.evaluationCollapsibleButton.enabled = True

    # Create evaluation fiducials and set them to the markups widgets
    self.logic.createFiducialLists()
    self.usFiducialList.setCurrentNode(self.logic.usFiducialsNode)
    self.mrFiducialList.setCurrentNode(self.logic.mrFiducialsNode)

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
  def onCalculateSegmentSimilarity(self):
    if self.logic.calculateSegmentSimilarity():
      # Show Dice results table in layout
      layoutManager = slicer.app.layoutManager()
      layoutManager.layout = slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpTableView
      tableView = layoutManager.tableWidget(0).tableView()
      tableView.setMRMLTableNode(self.logic.diceTableNode)
      # First four rows contain input information
      tableView.hideRow(0)
      tableView.hideRow(1)
      tableView.hideRow(2)
      tableView.hideRow(3)
      tableView.setColumnWidth(0,120)
    else:
      logging.error('Similarity calculation failed')

  #------------------------------------------------------------------------------
  def onCalculateFiducialErrors(self):
    if self.logic.calculateFiducialErrors():
      # Show fiducial errors table in layout
      layoutManager = slicer.app.layoutManager()
      layoutManager.layout = slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpTableView
      tableView = layoutManager.tableWidget(0).tableView()
      tableView.setMRMLTableNode(self.logic.fiducialErrorsTableNode)
      # First four rows may have been hidden for segment similarity results
      tableView.showRow(0)
      tableView.showRow(1)
      tableView.showRow(2)
      tableView.showRow(3)
    else:
      logging.error('Fiducial error calculation failed')

  #------------------------------------------------------------------------------
  def populateProstateSegmentCombobox(self, segmentationNode, prostateSegmentNameCombobox):
    validSegmentation = segmentationNode is not None and segmentationNode.GetSegmentation().GetNumberOfSegments() > 0
    prostateSegmentNameCombobox.clear()
    prostateSegmentNameCombobox.enabled = validSegmentation
    if not validSegmentation:
      return

    segmentIDs = vtk.vtkStringArray()
    segmentationNode.GetSegmentation().GetSegmentIDs(segmentIDs)
    for segmentIndex in xrange(0,segmentIDs.GetNumberOfValues()):
      segmentID = segmentIDs.GetValue(segmentIndex)
      segment = segmentationNode.GetSegmentation().GetSegment(segmentID)
      prostateSegmentNameCombobox.addItem(segment.GetName(),segmentID)

  #------------------------------------------------------------------------------
  def enter(self):
    """Runs whenever the module is reopened
    """
    # If data selection is empty, then select initial patients (with some heuristics by their name)
    if self.usVolumeNodeCombobox.currentNode() is None and self.usSegmentationNodeCombobox.currentNode() is None:
      self.selectInitialPatients()

  #------------------------------------------------------------------------------
  def exit(self):
    pass

  #------------------------------------------------------------------------------
  def selectInitialPatients(self):
    mrPatientItemCandidate = invalidShItemID
    usPatientItemCandidate = invalidShItemID
    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    children = vtk.vtkIdList()
    shNode.GetItemChildren(shNode.GetSceneItemID(), children)
    for i in xrange(children.GetNumberOfIds()):
      child = children.GetId(i)
      if shNode.GetItemLevel(child) == slicer.vtkMRMLSubjectHierarchyConstants.GetDICOMLevelPatient():
        # Try to guess patient selection by patient name
        name = shNode.GetItemName(child)
        if "US" in name and not usPatientItemCandidate:
          usPatientItemCandidate = child
        if "MR" in name and not mrPatientItemCandidate:
          mrPatientItemCandidate = child
    # Select guess if available, select first patient as US otherwise
    if usPatientItemCandidate:
      self.usPatientItemCombobox.setCurrentItem(usPatientItemCandidate)
      self.onUSPatientSelectionChanged(usPatientItemCandidate)
    if mrPatientItemCandidate:
      self.mrPatientItemCombobox.setCurrentItem(mrPatientItemCandidate)
      self.onMRPatientSelectionChanged(mrPatientItemCandidate)

  #------------------------------------------------------------------------------
  def onSelfTest(self):
    slicer.mrmlScene.Clear(0)
    tester = ProstateMRIUSContourPropagationTest()
    tester.widget = self
    tester.test_ProstateMRIUSContourPropagation_FullTest()

#
# -----------------------------------------------------------------------------
# ProstateMRIUSContourPropagationLogic
# -----------------------------------------------------------------------------
#

class ProstateMRIUSContourPropagationLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """

  def __init__(self):
    self.usPatientShItemID = invalidShItemID
    self.usProstateSegmentName = None
    self.usVolumeNode = None
    self.usVolumeHardenedNode = None
    self.usSegmentationNode = None
    self.usSegmentationHardenedNode = None
    self.usResampledVolumeNode = None
    self.usProstateLabelmap = None
    self.usFiducialsNode = None

    self.mrPatientShItemID = invalidShItemID
    self.mrProstateSegmentName = None
    self.mrVolumeNode = None
    self.mrSegmentationNode = None
    self.mrSegmentationHardenedNode = None
    self.mrCroppedVolumeNode = None
    self.mrProstateLabelmap = None
    self.mrFiducialsNode = None

    self.parsedUsPatientShItemID = invalidShItemID
    self.parsedMrPatientShItemID = invalidShItemID

    self.mrVolumeNodeForExport = None
    self.mrSegmentationNodeForMrExport = None
    self.usVolumeNodeForExport = None
    self.mrSegmentationNodeForUsExport = None
    # Flag determining whether the exported MR volume is resampled to match the US geometry or not
    self.resampleMrToUsGeometryForExport = False

    self.affineTransformNode = None
    self.bsplineTransformNode = None
    self.fiducialErrorsTableNode = None
    self.segmentComparisonNode = None
    self.diceTableNode = None
    self.hausdorffTableNode = None

    # Flag determining whether to keep temporary intermediate nodes in the scene
    # such as ROI, models, distance maps, smoothed volumes
    self.keepIntermediateNodes = False

  #------------------------------------------------------------------------------
  def performRegistration(self):
    logging.info('Performing registration workflow')
    self.cropMRI()
    self.preAlignSegmentations()
    self.resampleUS()
    self.createProstateContourLabelmaps()
    return self.performDistanceBasedRegistration()

  #------------------------------------------------------------------------------
  def parseUSPatient(self):
    if not self.usPatientShItemID:
      return
    if self.usPatientShItemID == self.parsedUsPatientShItemID:
      # Do not re-parse the patient, because any changed selection will be over-ridden by the default (which was not optimal, that's why the user changed it)
      return
    # Parse US patient
    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    self.usVolumeNode = None
    self.usSegmentationNode = None
    usSeriesCollection = vtk.vtkCollection()
    shNode.GetDataNodesInBranch(self.usPatientShItemID, usSeriesCollection)
    for i in xrange(0,usSeriesCollection.GetNumberOfItems()):
      currentDataNode = usSeriesCollection.GetItemAsObject(i)
      if currentDataNode.IsA('vtkMRMLScalarVolumeNode') and not currentDataNode.IsA('vtkMRMLSegmentationNode'):
        currentSeriesItemID = shNode.GetItemByDataNode(currentDataNode)
        if shNode.GetItemAttribute(currentSeriesItemID, slicer.vtkMRMLSubjectHierarchyConstants.GetDICOMSeriesModalityAttributeName()) == 'US':
          self.usVolumeNode = currentDataNode
      if currentDataNode.IsA('vtkMRMLSegmentationNode'):
        self.usSegmentationNode = currentDataNode
    self.parsedUsPatientShItemID = self.usPatientShItemID

  #------------------------------------------------------------------------------
  def parseMRPatient(self):
    if not self.mrPatientShItemID:
      return
    if self.mrPatientShItemID == self.parsedMrPatientShItemID:
      # Do not re-parse the patient, because any changed selection will be over-ridden by the default (which was not optimal, that's why the user changed it)
      return
    # Parse MRI patient
    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    self.mrVolumeNode = None
    self.mrSegmentationNode = None
    mrSeriesCollection = vtk.vtkCollection()
    shNode.GetDataNodesInBranch(self.mrPatientShItemID, mrSeriesCollection)
    for i in xrange(0,mrSeriesCollection.GetNumberOfItems()):
      currentDataNode = mrSeriesCollection.GetItemAsObject(i)
      if currentDataNode.IsA('vtkMRMLScalarVolumeNode') and not currentDataNode.IsA('vtkMRMLSegmentationNode'):
        currentSeriesItemID = shNode.GetItemByDataNode(currentDataNode)
        if shNode.GetItemAttribute(currentSeriesItemID, slicer.vtkMRMLSubjectHierarchyConstants.GetDICOMSeriesModalityAttributeName()) == 'MR':
          self.mrVolumeNode = currentDataNode
      if currentDataNode.IsA('vtkMRMLSegmentationNode'):
        self.mrSegmentationNode = currentDataNode
    self.parsedMrPatientShItemID = self.mrPatientShItemID

  #------------------------------------------------------------------------------
  def cropMRI(self):
    logging.info('Cropping MRI volume')
    if not self.mrVolumeNode or not self.mrSegmentationNode:
      logging.error('Unable to access MR volume or segmentation')
      return

    # Create ROI
    roiNode = slicer.vtkMRMLAnnotationROINode()
    roiNode.SetName('CropROI_' + self.mrVolumeNode.GetName())
    slicer.mrmlScene.AddNode(roiNode)

    # Determine ROI position
    bounds = [0]*6
    self.mrSegmentationNode.GetSegmentation().GetBounds(bounds)
    center = [(bounds[0]+bounds[1])/2, (bounds[2]+bounds[3])/2, (bounds[4]+bounds[5])/2]
    roiNode.SetXYZ(center[0], center[1], center[2])

    # Determine ROI size (add prostate width along RL axis, square slice, add height/2 along IS)
    #TODO: Support tilted volumes
    prostateLR3 = (bounds[1]-bounds[0]) * 3
    prostateIS2 = (bounds[5]-bounds[4]) * 2
    radius = [prostateLR3/2, prostateLR3/2, prostateIS2/2]
    roiNode.SetRadiusXYZ(radius[0], radius[1], radius[2])

    # Crop MRI volume
    cropParams = slicer.vtkMRMLCropVolumeParametersNode()
    cropParams.SetInputVolumeNodeID(self.mrVolumeNode.GetID())
    cropParams.SetROINodeID(roiNode.GetID())
    cropParams.SetVoxelBased(True)
    slicer.mrmlScene.AddNode(cropParams)
    cropLogic = slicer.modules.cropvolume.logic()
    cropLogic.Apply(cropParams)

    # Add resampled MRI volume and cropping ROI to the same study as the original MR
    self.mrCroppedVolumeNode = cropParams.GetOutputVolumeNode()
    if self.mrCroppedVolumeNode is None:
      logging.error('Unable to access cropped MR volume')
      return
    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    mrStudyItemID = shNode.GetItemParent(shNode.GetItemByDataNode(self.mrVolumeNode))
    croppedMrShItemID = shNode.GetItemByDataNode(self.mrCroppedVolumeNode)
    if not croppedMrShItemID:
      logging.error('Unable to access cropped MR subject hierarchy item')
      return
    shNode.SetItemParent(croppedMrShItemID, mrStudyItemID)

    if not self.keepIntermediateNodes:
      slicer.mrmlScene.RemoveNode(roiNode)
    else:
      roiShItemID = shNode.GetItemByDataNode(roiNode)
      if not roiShItemID:
        logging.error('Unable to access crop ROI subject hierarchy item')
        return
      shNode.SetItemParent(roiShItemID, mrStudyItemID)

      # Hide ROI by default
      shNode.SetDisplayVisibilityForBranch(roiShItemID, 0)

  #------------------------------------------------------------------------------
  def preAlignSegmentations(self):
    logging.info('Pre-aligning segmentations')
    if self.mrSegmentationNode is None or self.mrVolumeNode is None or self.mrCroppedVolumeNode is None or self.usSegmentationNode is None:
      logging.error('Invalid data selection')
      return
    # Get center of segmentation bounding boxes
    usBounds = [0]*6
    usProstateSegmentID = self.usSegmentationNode.GetSegmentation().GetSegmentIdBySegmentName(self.usProstateSegmentName)
    usProstateSegment = self.usSegmentationNode.GetSegmentation().GetSegment(usProstateSegmentID)
    if usProstateSegment is None:
      logging.error('Failed to get US prostate segment')
      return
    usProstateSegment.GetBounds(usBounds)
    usProstateCenter = [(usBounds[1]+usBounds[0])/2, (usBounds[3]+usBounds[2])/2, (usBounds[5]+usBounds[4])/2]
    logging.info('US prostate bounds: ' + repr(usBounds))
    mrBounds = [0]*6
    mrProstateSegmentID = self.mrSegmentationNode.GetSegmentation().GetSegmentIdBySegmentName(self.mrProstateSegmentName)
    mrProstateSegment = self.mrSegmentationNode.GetSegmentation().GetSegment(mrProstateSegmentID)
    if mrProstateSegment is None:
      logging.error('Failed to get MR prostate segment')
      return
    mrProstateSegment.GetBounds(mrBounds)
    mrProstateCenter = [(mrBounds[1]+mrBounds[0])/2, (mrBounds[3]+mrBounds[2])/2, (mrBounds[5]+mrBounds[4])/2]
    logging.info('MRI prostate bounds: ' + repr(mrBounds))

    # Create alignment transform
    mri2UsTranslation = [usProstateCenter[0]-mrProstateCenter[0], usProstateCenter[1]-mrProstateCenter[1], usProstateCenter[2]-mrProstateCenter[2]]
    logging.info('MRI to US prostate translation: ' + repr(mri2UsTranslation))
    self.preAlignmentMri2UsLinearTransform = slicer.vtkMRMLLinearTransformNode()
    self.preAlignmentMri2UsLinearTransform.SetName(slicer.mrmlScene.GenerateUniqueName('PreAlignmentMri2UsLinearTransform'))
    slicer.mrmlScene.AddNode(self.preAlignmentMri2UsLinearTransform)
    mri2UsMatrix = vtk.vtkMatrix4x4()
    mri2UsMatrix.SetElement(0,3,mri2UsTranslation[0])
    mri2UsMatrix.SetElement(1,3,mri2UsTranslation[1])
    mri2UsMatrix.SetElement(2,3,mri2UsTranslation[2])
    self.preAlignmentMri2UsLinearTransform.SetAndObserveMatrixTransformToParent(mri2UsMatrix)

    #TODO: This snippet shows both ROIs for testing purposes
    # roi1Node = slicer.vtkMRMLAnnotationROINode()
    # roi1Node.SetName(slicer.mrmlScene.GenerateUniqueName('UsBounds'))
    # slicer.mrmlScene.AddNode(roi1Node)
    # roi1Node.SetXYZ(usProstateCenter[0], usProstateCenter[1], usProstateCenter[2])
    # roi1Node.SetRadiusXYZ((usBounds[1]-usBounds[0])/2, (usBounds[3]-usBounds[2])/2, (usBounds[5]-usBounds[4])/2)
    # roi2Node = slicer.vtkMRMLAnnotationROINode()
    # roi2Node.SetName(slicer.mrmlScene.GenerateUniqueName('MrBounds'))
    # slicer.mrmlScene.AddNode(roi2Node)
    # roi2Node.SetXYZ(mrProstateCenter[0], mrProstateCenter[1], mrProstateCenter[2])
    # roi2Node.SetRadiusXYZ((mrBounds[1]-mrBounds[0])/2, (mrBounds[3]-mrBounds[2])/2, (mrBounds[5]-mrBounds[4])/2)
    # return

    # Apply transform to US image and segmentation
    self.mrVolumeNode.SetAndObserveTransformNodeID(self.preAlignmentMri2UsLinearTransform.GetID())
    self.mrSegmentationNode.SetAndObserveTransformNodeID(self.preAlignmentMri2UsLinearTransform.GetID())
    self.mrCroppedVolumeNode.SetAndObserveTransformNodeID(self.preAlignmentMri2UsLinearTransform.GetID())

    # Harden transform
    slicer.vtkSlicerTransformLogic.hardenTransform(self.mrVolumeNode)
    slicer.vtkSlicerTransformLogic.hardenTransform(self.mrSegmentationNode)
    slicer.vtkSlicerTransformLogic.hardenTransform(self.mrCroppedVolumeNode)

  #------------------------------------------------------------------------------
  def resampleUS(self):
    logging.info('Resampling US volume')
    if not self.usVolumeNode:
      logging.error('Unable to access US volume')
      return

    # Create output volume
    self.usResampledVolumeNode = slicer.vtkMRMLScalarVolumeNode()
    self.usResampledVolumeNode.SetName(self.usVolumeNode.GetName() + '_Resampled_1x1x1mm')
    slicer.mrmlScene.AddNode(self.usResampledVolumeNode)

    # Clone input volume and harden transform if any (the CLI does not handle parent transforms)
    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    usVolumeShItemID = shNode.GetItemByDataNode(self.usVolumeNode)
    usVolumeNodeCloneName = self.usVolumeNode.GetName() + '_HardenedCopy'
    usVolumeHardenedShItemID = slicer.vtkSlicerSubjectHierarchyModuleLogic.CloneSubjectHierarchyItem(shNode, usVolumeShItemID, usVolumeNodeCloneName)
    shNode.SetItemParent(usVolumeHardenedShItemID, shNode.GetItemParent(usVolumeShItemID))
    self.usVolumeHardenedNode = shNode.GetItemDataNode(usVolumeHardenedShItemID)
    slicer.vtkSlicerTransformLogic.hardenTransform(self.usVolumeHardenedNode)

    # Resample
    resampleParameters = {'outputPixelSpacing':'1,1,1', 'interpolationType':'lanczos', 'InputVolume':self.usVolumeHardenedNode.GetID(), 'OutputVolume':self.usResampledVolumeNode.GetID()}
    slicer.cli.run(slicer.modules.resamplescalarvolume, None, resampleParameters, wait_for_completion=True)

    # Add resampled US volume to the same study as the original US
    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    usStudyItemID = shNode.GetItemParent(shNode.GetItemByDataNode(self.usVolumeNode))
    resampledUsShItemID = shNode.GetItemByDataNode(self.usResampledVolumeNode)
    if not resampledUsShItemID:
      logging.error('Unable to access resampled US subject hierarchy item')
      return
    shNode.SetItemParent(resampledUsShItemID, usStudyItemID)

  #------------------------------------------------------------------------------
  def createProstateContourLabelmaps(self):
    logging.info('Creating prostate contour labelmaps')
    if self.mrSegmentationNode is None or self.usSegmentationNode is None:
      logging.error('Unable to access segmentations')

    # Clone segmentations and harden transform if any (so that the labelmap geometry is correct)
    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    mrSegmentationShItemID = shNode.GetItemByDataNode(self.mrSegmentationNode)
    mrSegmentationNodeCloneName = self.mrSegmentationNode.GetName() + '_HardenedCopy'
    mrSegmentationHardenedShItemID = slicer.vtkSlicerSubjectHierarchyModuleLogic.CloneSubjectHierarchyItem(shNode, mrSegmentationShItemID, mrSegmentationNodeCloneName)
    shNode.SetItemParent(mrSegmentationHardenedShItemID, shNode.GetItemParent(mrSegmentationShItemID))
    self.mrSegmentationHardenedNode = shNode.GetItemDataNode(mrSegmentationHardenedShItemID)
    slicer.vtkSlicerTransformLogic.hardenTransform(self.mrSegmentationHardenedNode)
    usSegmentationShItemID = shNode.GetItemByDataNode(self.usSegmentationNode)
    usSegmentationNodeCloneName = self.usSegmentationNode.GetName() + '_HardenedCopy'
    usSegmentationHardenedShItemID = slicer.vtkSlicerSubjectHierarchyModuleLogic.CloneSubjectHierarchyItem(shNode, usSegmentationShItemID, usSegmentationNodeCloneName)
    shNode.SetItemParent(usSegmentationHardenedShItemID, shNode.GetItemParent(usSegmentationShItemID))
    self.usSegmentationHardenedNode = shNode.GetItemDataNode(usSegmentationHardenedShItemID)
    slicer.vtkSlicerTransformLogic.hardenTransform(self.usSegmentationHardenedNode)

    # Make sure the prostate segmentations have the labelmaps
    self.mrSegmentationHardenedNode.GetSegmentation().CreateRepresentation(slicer.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName())
    self.usSegmentationHardenedNode.GetSegmentation().CreateRepresentation(slicer.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName())
    # Get labelmap oriented image data
    mrProstateOrientedImageData = slicer.vtkOrientedImageData()
    mrProstateSegmentID = self.mrSegmentationHardenedNode.GetSegmentation().GetSegmentIdBySegmentName(self.mrProstateSegmentName)
    mrProstateOrientedImageData.DeepCopy(self.mrSegmentationHardenedNode.GetSegmentation().GetSegment(mrProstateSegmentID).GetRepresentation(slicer.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName()))
    usProstateOrientedImageData = slicer.vtkOrientedImageData()
    usProstateSegmentID = self.usSegmentationHardenedNode.GetSegmentation().GetSegmentIdBySegmentName(self.usProstateSegmentName)
    usProstateOrientedImageData.DeepCopy(self.usSegmentationHardenedNode.GetSegmentation().GetSegment(usProstateSegmentID).GetRepresentation(slicer.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName()))

    # Get MR volume geometry
    mrOrientedImageData = slicer.vtkSlicerSegmentationsModuleLogic.CreateOrientedImageDataFromVolumeNode(self.mrCroppedVolumeNode)
    mrOrientedImageData.UnRegister(None)

    # Ensure same geometry of oriented image data
    if not slicer.vtkOrientedImageDataResample.DoGeometriesMatch(mrProstateOrientedImageData, mrOrientedImageData) \
        or not slicer.vtkOrientedImageDataResample.DoExtentsMatch(mrProstateOrientedImageData, mrOrientedImageData):
      slicer.vtkOrientedImageDataResample.ResampleOrientedImageToReferenceOrientedImage(mrProstateOrientedImageData, mrOrientedImageData, mrProstateOrientedImageData)
    if not slicer.vtkOrientedImageDataResample.DoGeometriesMatch(usProstateOrientedImageData, mrOrientedImageData) \
        or not slicer.vtkOrientedImageDataResample.DoExtentsMatch(usProstateOrientedImageData, mrOrientedImageData):
      slicer.vtkOrientedImageDataResample.ResampleOrientedImageToReferenceOrientedImage(usProstateOrientedImageData, mrOrientedImageData, usProstateOrientedImageData)

    # Export segment binary labelmaps to labelmap nodes
    self.usProstateLabelmap = slicer.vtkMRMLLabelMapVolumeNode()
    self.usProstateLabelmap.SetName(slicer.mrmlScene.GenerateUniqueName('US_Prostate_Padded'))
    slicer.mrmlScene.AddNode(self.usProstateLabelmap)
    self.usProstateLabelmap.CreateDefaultDisplayNodes()

    self.mrProstateLabelmap = slicer.vtkMRMLLabelMapVolumeNode()
    self.mrProstateLabelmap.SetName(slicer.mrmlScene.GenerateUniqueName('MRI_Prostate_Padded'))
    slicer.mrmlScene.AddNode(self.mrProstateLabelmap)
    self.mrProstateLabelmap.CreateDefaultDisplayNodes()

    ret1 = slicer.vtkSlicerSegmentationsModuleLogic.CreateLabelmapVolumeFromOrientedImageData(usProstateOrientedImageData, self.usProstateLabelmap)
    ret2 = slicer.vtkSlicerSegmentationsModuleLogic.CreateLabelmapVolumeFromOrientedImageData(mrProstateOrientedImageData, self.mrProstateLabelmap)
    if ret1 is False or ret2 is False:
      logging.error('Failed to create prostate labelmap nodes')

    # Add labelmaps to the corresponding studies in subject hierarchy
    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    usStudyItemID = shNode.GetItemParent(shNode.GetItemByDataNode(self.usVolumeNode))
    mrStudyItemID = shNode.GetItemParent(shNode.GetItemByDataNode(self.mrVolumeNode))
    usLabelmapShItemID = shNode.GetItemByDataNode(self.usProstateLabelmap)
    mrLabelmapShItemID = shNode.GetItemByDataNode(self.mrProstateLabelmap)
    if not usLabelmapShItemID or not mrLabelmapShItemID:
      logging.error('Unable to access subject hierarchy items for the prostate labelmaps')
      return
    shNode.SetItemParent(usLabelmapShItemID, usStudyItemID)
    shNode.SetItemParent(mrLabelmapShItemID, mrStudyItemID)

  #------------------------------------------------------------------------------
  def performDistanceBasedRegistration(self):
    logging.info('Performing distance based registration')

    # Register using Distance Map Based Registration
    slicer.modules.distancemapbasedregistration.createNewWidgetRepresentation()
    distMapRegModuleWidget = slicer.modules.DistanceMapBasedRegistrationWidget
    distMapRegModuleWidget.fixedImageSelector.setCurrentNode(self.usVolumeNode)
    distMapRegModuleWidget.fixedImageLabelSelector.setCurrentNode(self.usProstateLabelmap)
    distMapRegModuleWidget.movingImageSelector.setCurrentNode(self.mrVolumeNode)
    distMapRegModuleWidget.movingImageLabelSelector.setCurrentNode(self.mrProstateLabelmap)
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
    slicer.mrmlScene.RemoveNode(self.mrCroppedVolumeNode)
    slicer.mrmlScene.RemoveNode(self.usResampledVolumeNode)
    slicer.mrmlScene.RemoveNode(self.usProstateLabelmap)
    slicer.mrmlScene.RemoveNode(self.mrProstateLabelmap)
    slicer.mrmlScene.RemoveNode(self.usVolumeHardenedNode)
    slicer.mrmlScene.RemoveNode(self.mrSegmentationHardenedNode)
    slicer.mrmlScene.RemoveNode(self.usSegmentationHardenedNode)

    # Remove nodes created by distance based registration
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('US_Prostate_Padded-Cropped'))
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('US_Prostate_Padded-Smoothed'))
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('US_Prostate_Padded-DistanceMap'))
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('US_Prostate_Padded-surface'))
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('MRI_Prostate_Padded-Cropped'))
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('MRI_Prostate_Padded-Smoothed'))
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('MRI_Prostate_Padded-DistanceMap'))
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('MRI_Prostate_Padded-surface'))
    slicer.mrmlScene.RemoveNode(slicer.util.getNode('MovingImageCopy'))

  #------------------------------------------------------------------------------
  def createFiducialLists(self):
    # Create or get fiducial nodes for evaluation
    self.markupsLogic = slicer.modules.markups.logic()

    usFiducialsNodeId = self.markupsLogic.AddNewFiducialNode('US fiducials')
    self.usFiducialsNode = slicer.mrmlScene.GetNodeByID(usFiducialsNodeId)
    usFiducialsDisplayNode = self.usFiducialsNode.GetDisplayNode()
    usFiducialsDisplayNode.SetSelectedColor(1.0, 0.0, 0.0)

    mrFiducialsNodeId = self.markupsLogic.AddNewFiducialNode('MRI fiducials')
    self.mrFiducialsNode = slicer.mrmlScene.GetNodeByID(mrFiducialsNodeId)
    mrFiducialsDisplayNode = self.mrFiducialsNode.GetDisplayNode()
    mrFiducialsDisplayNode.SetSelectedColor(0, 0.67, 1.0)

  #------------------------------------------------------------------------------
  def applyNoTransformation(self):
    if self.mrVolumeNode is None or self.mrSegmentationNode is None:
      logging.error('Failed to apply transformation on MR volume and segmentation')
    # Apply transform on MR volume and segmentation
    self.mrVolumeNode.SetAndObserveTransformNodeID(None)
    self.mrSegmentationNode.SetAndObserveTransformNodeID(None)

  #------------------------------------------------------------------------------
  def applyRigidTransformation(self):
    if self.mrVolumeNode is None or self.mrSegmentationNode is None:
      logging.error('Failed to apply transformation on MR volume and segmentation')
    # Apply transform on MR volume and segmentation
    self.mrVolumeNode.SetAndObserveTransformNodeID(self.affineTransformNode.GetID())
    self.mrSegmentationNode.SetAndObserveTransformNodeID(self.affineTransformNode.GetID())

  #------------------------------------------------------------------------------
  def applyDeformableTransformation(self):
    if self.mrVolumeNode is None or self.mrSegmentationNode is None:
      logging.error('Failed to apply transformation on MR volume and segmentation')
    # Apply transform on MR volume and segmentation
    self.mrVolumeNode.SetAndObserveTransformNodeID(self.bsplineTransformNode.GetID())
    self.mrSegmentationNode.SetAndObserveTransformNodeID(self.bsplineTransformNode.GetID())

  #------------------------------------------------------------------------------
  def exportDeformedMrStudyToDicom(self):
    if not self.mrPatientShItemID or self.mrVolumeNode is None or self.mrSegmentationNode is None:
      logging.error('Unable to access MRI data for DICOM export')
      return
    if self.bsplineTransformNode is None:
      logging.error('Unable to access registration result')
      return

    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    if self.mrVolumeNodeForExport is None and self.mrSegmentationNodeForMrExport is None:
      # Create new study for deformed MR volume and segmentation
      deformedMrStudyShItemID = shNode.CreateStudyItem(shNode.GetSceneItemID(), 'Deformed MRI Study')
      shNode.SetItemParent(deformedMrStudyShItemID, self.mrPatientShItemID)

      # Clone MR segmentation into new study
      mrSegmentationShItemID = shNode.GetItemByDataNode(self.mrSegmentationNode)
      mrSegmentationNodeCloneName = self.mrSegmentationNode.GetName() + ' For Export with MRI'
      mrSegmentationForMrExportShItemID = slicer.vtkSlicerSubjectHierarchyModuleLogic.CloneSubjectHierarchyItem(shNode, mrSegmentationShItemID, mrSegmentationNodeCloneName)
      shNode.SetItemParent(mrSegmentationForMrExportShItemID, deformedMrStudyShItemID)
      self.mrSegmentationNodeForMrExport = shNode.GetItemDataNode(mrSegmentationForMrExportShItemID)

      # Clone MR volume into the new study
      self.mrVolumeNodeForExport = slicer.vtkMRMLScalarVolumeNode()
      mrVolumeNodeForExportName = self.mrVolumeNode.GetName() + ' For Export'
      self.mrVolumeNodeForExport.SetName(mrVolumeNodeForExportName)
      slicer.mrmlScene.AddNode(self.mrVolumeNodeForExport)
      # Set modality tag for the volume item
      mrVolumeNodeForExportShItemID = shNode.GetItemByDataNode(self.mrVolumeNodeForExport)
      shNode.SetItemAttribute( mrVolumeNodeForExportShItemID,
        slicer.vtkMRMLSubjectHierarchyConstants.GetDICOMSeriesModalityAttributeName(), 'MR' )

      if self.resampleMrToUsGeometryForExport:
        # Create resampled MR volume in US reference frame so that the exported structure set is smoother
        # (more fidelity to the original segmentation, in the granularity of the reference US image where the procedure is done)
        mrVolumeNodeCurrentTransformNode = self.mrVolumeNode.GetParentTransformNode() # So that we can set restore it later
        self.mrVolumeNode.SetAndObserveTransformNodeID(self.bsplineTransformNode.GetID()) # Make sure the deformable transform is the parent when copying
        mrOrientedImageData = slicer.vtkSlicerSegmentationsModuleLogic.CreateOrientedImageDataFromVolumeNode(self.mrVolumeNode)
        slicer.vtkOrientedImageDataResample.ResampleOrientedImageToReferenceOrientedImage(mrOrientedImageData, usOrientedImageData, mrOrientedImageData, True, True)
        mrImageToWorldMatrix = vtk.vtkMatrix4x4()
        mrOrientedImageData.GetImageToWorldMatrix(mrImageToWorldMatrix)
        self.mrVolumeNodeForExport.SetIJKToRASMatrix(mrImageToWorldMatrix)
        identityMatrix = vtk.vtkMatrix4x4()
        identityMatrix.Identity()
        mrOrientedImageData.SetGeometryFromImageToWorldMatrix(identityMatrix)
        slicer.vtkMRMLSegmentationNode.ShiftVolumeNodeExtentToZeroStart(self.mrVolumeNodeForExport)
        self.mrVolumeNodeForExport.SetAndObserveImageData(mrOrientedImageData)
        self.mrVolumeNode.SetAndObserveTransformNodeID(mrVolumeNodeCurrentTransformNode)
      else:
        self.mrVolumeNodeForExport.Copy(self.mrVolumeNode)
        self.mrVolumeNodeForExport.SetAndObserveTransformNodeID(self.bsplineTransformNode.GetID())

      mrVolumeForExportShItemID = shNode.GetItemByDataNode(self.mrVolumeNodeForExport)
      shNode.SetItemParent(mrVolumeForExportShItemID, deformedMrStudyShItemID)

    elif int(self.mrVolumeNodeForExport is None) + int(self.mrSegmentationNodeForMrExport is None) == 1:
      # If only one of them exist, then there is an inconsistency
      logging.error('Critical inconsistency error! Only some of the data to export is found')
      return
    else:
      # All data exist for export. Get the study item for the export
      mrSegmentationForMrExportShItemID = shNode.GetItemByDataNode(self.mrSegmentationNodeForMrExport)
      mrVolumeForExportShItemID = shNode.GetItemByDataNode(self.mrVolumeNodeForExport)
      if shNode.GetItemParent(mrSegmentationForMrExportShItemID) != shNode.GetItemParent(mrVolumeForExportShItemID):
        logging.error('Inconsistency error! The data to export are not in the same subject hierarchy branch')
        return
      deformedMrStudyShItemID = shNode.GetItemParent(mrSegmentationForMrExportShItemID)

    # Open DICOM export dialog, selecting the study to export
    exportDicomDialog = slicer.qSlicerDICOMExportDialog(None)
    exportDicomDialog.setMRMLScene(slicer.mrmlScene)
    exportDicomDialog.execDialog(deformedMrStudyShItemID)

  #------------------------------------------------------------------------------
  def exportDeformedUsStudyToDicom(self):
    if not self.usPatientShItemID or self.usVolumeNode is None or self.mrSegmentationNode is None:
      logging.error('Unable to access US data for DICOM export')
      return
    if self.bsplineTransformNode is None:
      logging.error('Unable to access registration result')
      return

    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    if self.usVolumeNodeForExport is None and self.mrSegmentationNodeForUsExport is None:
      # Create new study for US volume and deformed MR segmentation
      usStudyWithMrStructuresShItemID = shNode.CreateStudyItem(shNode.GetSceneItemID(), 'US Study with MRI structures')
      shNode.SetItemParent(usStudyWithMrStructuresShItemID, self.usPatientShItemID)

      # Clone MR segmentation into new study
      mrSegmentationShItemID = shNode.GetItemByDataNode(self.mrSegmentationNode)
      mrSegmentationNodeCloneName = self.mrSegmentationNode.GetName() + ' For Export with US'
      mrSegmentationForUsExportShItemID = slicer.vtkSlicerSubjectHierarchyModuleLogic.CloneSubjectHierarchyItem(shNode, mrSegmentationShItemID, mrSegmentationNodeCloneName)
      shNode.SetItemParent(mrSegmentationForUsExportShItemID, usStudyWithMrStructuresShItemID)
      self.mrSegmentationNodeForUsExport = shNode.GetItemDataNode(mrSegmentationForUsExportShItemID)

      # Set US volume geometry for labelmap conversion and create labelmap using that geometry
      # usOrientedImageData = vtkSlicerSegmentationsModuleLogic.vtkSlicerSegmentationsModuleLogic.CreateOrientedImageDataFromVolumeNode(self.usVolumeNode)
      # usGeometry = vtkSegmentationCore.vtkSegmentationConverter.SerializeImageGeometry(usOrientedImageData)
      # self.mrSegmentationNodeForUsExport.GetSegmentation().RemoveRepresentation(vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName())
      # self.mrSegmentationNodeForUsExport.GetSegmentation().CreateRepresentation(vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName())
      # self.mrSegmentationNodeForUsExport.SetAndObserveTransformNodeID(self.bsplineTransformNode.GetID()) # Make sure the deformable transform is the parent when exporting

      # Clone MR volume into the new study
      self.usVolumeNodeForExport = slicer.vtkMRMLScalarVolumeNode()
      usVolumeNodeForExportName = self.usVolumeNode.GetName() + ' For Export'
      self.usVolumeNodeForExport.SetName(usVolumeNodeForExportName)
      slicer.mrmlScene.AddNode(self.usVolumeNodeForExport)
      # Set modality tag for the volume item
      usVolumeNodeForExportShItemID = shNode.GetItemByDataNode(self.usVolumeNodeForExport)
      shNode.SetItemAttribute( usVolumeNodeForExportShItemID,
        slicer.vtkMRMLSubjectHierarchyConstants.GetDICOMSeriesModalityAttributeName(), 'US' )

      self.usVolumeNodeForExport.Copy(self.usVolumeNode)

      usVolumeForExportShItemID = shNode.GetItemByDataNode(self.usVolumeNodeForExport)
      shNode.SetItemParent(usVolumeForExportShItemID, usStudyWithMrStructuresShItemID)

    elif int(self.usVolumeNodeForExport is None) + int(self.mrSegmentationNodeForUsExport is None) == 1:
      # If only one of them exist, then there is an inconsistency
      logging.error('Critical inconsistency error! Only some of the data to export is found')
      return
    else:
      # All data exist for export. Get the study item for the export
      mrSegmentationForUsExportShItemID = shNode.GetItemByDataNode(self.mrSegmentationNodeForUsExport)
      usVolumeForExportShItemID = shNode.GetItemByDataNode(self.usVolumeNodeForExport)
      if shNode.GetItemParent(mrSegmentationForUsExportShItemID) != shNode.GetItemParent(usVolumeForExportShItemID):
        logging.error('Inconsistency error! The data to export are not in the same subject hierarchy branch')
        return
      usStudyWithMrStructuresShItemID = shNode.GetItemParent(mrSegmentationForUsExportShItemID)

    # Open DICOM export dialog, selecting the study to export
    exportDicomDialog = slicer.qSlicerDICOMExportDialog(None)
    exportDicomDialog.setMRMLScene(slicer.mrmlScene)
    exportDicomDialog.execDialog(usStudyWithMrStructuresShItemID)

  #------------------------------------------------------------------------------
  def setupResultVisualization(self):
    logging.info('Setting up result visualization')
    if self.usSegmentationNode is None or self.mrSegmentationNode is None:
      logging.error('Failed to get segmentations')
      return
    usProstateSegmentID = self.usSegmentationNode.GetSegmentation().GetSegmentIdBySegmentName(self.usProstateSegmentName)
    usProstateSegment = self.usSegmentationNode.GetSegmentation().GetSegment(usProstateSegmentID)
    mrProstateSegmentID = self.mrSegmentationNode.GetSegmentation().GetSegmentIdBySegmentName(self.mrProstateSegmentName)
    mrProstateSegment = self.mrSegmentationNode.GetSegmentation().GetSegment(mrProstateSegmentID)
    if usProstateSegment is None or mrProstateSegment is None:
      logging.error('Failed to get prostate segments')
      return

    # Make US prostate segment red with 50% opacity
    usProstateSegment.SetColor(1.0,0.0,0.0)
    usSegmentationDisplayNode = self.usSegmentationNode.GetDisplayNode()
    if usSegmentationDisplayNode is None:
      logging.error('Failed to get US segmentation display node')
      return
    usSegmentationDisplayNode.SetSegmentOpacity(usProstateSegmentID, 0.5)

    # Make MR prostate segment light blue with 50% opacity
    mrProstateSegment.SetColor(0.43,0.72,0.82)
    mrSegmentationDisplayNode = self.mrSegmentationNode.GetDisplayNode()
    if mrSegmentationDisplayNode is None:
      logging.error('Failed to get MRI segmentation display node')
      return
    mrSegmentationDisplayNode.SetSegmentOpacity(mrProstateSegmentID, 0.5)

  #------------------------------------------------------------------------------
  def calculateSegmentSimilarity(self):
    logging.info('Calculating prostate similarity')
    if self.usSegmentationNode is None or self.mrSegmentationNode is None:
      logging.error('Failed to get segmentations')
      return False

    # Calculate Dice, Hausdorff
    if self.segmentComparisonNode is None or self.segmentComparisonNode.GetScene() is None:
      self.segmentComparisonNode = slicer.vtkMRMLSegmentComparisonNode()
      self.segmentComparisonNode.SetName(slicer.mrmlScene.GenerateUniqueName('MRI-US_SegmentComparison'))
      slicer.mrmlScene.AddNode(self.segmentComparisonNode)
    if self.diceTableNode is None:
      self.diceTableNode = slicer.vtkMRMLTableNode()
      self.diceTableNode.SetName('Dice comparison results table')
      slicer.mrmlScene.AddNode(self.diceTableNode)
    if self.hausdorffTableNode is None:
      self.hausdorffTableNode = slicer.vtkMRMLTableNode()
      self.hausdorffTableNode.SetName('Hausdorff comparison results table')
      slicer.mrmlScene.AddNode(self.hausdorffTableNode)
    self.segmentComparisonNode.SetAndObserveDiceTableNode(self.diceTableNode)
    self.segmentComparisonNode.SetAndObserveHausdorffTableNode(self.hausdorffTableNode)

    segmentComparisonLogic = slicer.modules.segmentcomparison.logic()

    self.segmentComparisonNode.SetAndObserveReferenceSegmentationNode(self.usSegmentationNode)
    usProstateSegmentID = self.usSegmentationNode.GetSegmentation().GetSegmentIdBySegmentName(self.usProstateSegmentName)
    self.segmentComparisonNode.SetReferenceSegmentID(usProstateSegmentID)
    self.segmentComparisonNode.SetAndObserveCompareSegmentationNode(self.mrSegmentationNode)
    mrProstateSegmentID = self.mrSegmentationNode.GetSegmentation().GetSegmentIdBySegmentName(self.mrProstateSegmentName)
    self.segmentComparisonNode.SetCompareSegmentID(mrProstateSegmentID)

    diceError = segmentComparisonLogic.ComputeDiceStatistics(self.segmentComparisonNode)
    hausdorffError = segmentComparisonLogic.ComputeHausdorffDistances(self.segmentComparisonNode)

    if diceError != '':
      logging.error('Failed to calculate Dice similarity: ' + diceError)
      return False
    if hausdorffError != '':
      logging.error('Failed to calculate Hausdorff similarity: ' + hausdorffError)
      return False

    return True

  #------------------------------------------------------------------------------
  def calculateFiducialErrors(self):
    logging.info('Calculating fiducial errors')
    # Verify fiducial lists
    if self.usFiducialsNode is None or self.mrFiducialsNode is None:
      logging.error('Invalid fidicual nodes')
      return False
    if self.usFiducialsNode.GetNumberOfFiducials() != self.mrFiducialsNode.GetNumberOfFiducials():
      errorMessage = 'Fiducial lists need to contain the same number of fiducials'
      logging.error(errorMessage)
      qt.QMessageBox.critical(None, 'Fiducial evaluation failed', errorMessage)
      return False
    if self.usFiducialsNode.GetNumberOfFiducials() == 0 or self.mrFiducialsNode.GetNumberOfFiducials() == 0:
      errorMessage = 'Fiducial lists need to contain at least one fiducial'
      logging.error(errorMessage)
      qt.QMessageBox.critical(None, 'Fiducial evaluation failed', errorMessage)
      return False

    # Create result table node
    self.fiducialErrorsTableNode = slicer.vtkMRMLTableNode()
    name = slicer.mrmlScene.GenerateUniqueName('Fiducial errors table')
    self.fiducialErrorsTableNode.SetName(name)
    self.fiducialErrorsTableNode.SetUseFirstColumnAsRowHeader(True)
    self.fiducialErrorsTableNode.SetUseColumnNameAsColumnHeader(True)
    slicer.mrmlScene.AddNode(self.fiducialErrorsTableNode)

    # Row headers
    header = self.fiducialErrorsTableNode.AddColumn()
    header.InsertNextValue("3D")
    header.InsertNextValue("2D R-L")
    header.InsertNextValue("2D A-P")
    header.InsertNextValue("2D I-S")

    # Calculate error metrics
    for index in xrange(self.usFiducialsNode.GetNumberOfFiducials()):
      usPos = [0,0,0]
      self.usFiducialsNode.GetNthFiducialPosition(index,usPos)
      mrPos = [0,0,0]
      self.mrFiducialsNode.GetNthFiducialPosition(index,mrPos)
      column = self.fiducialErrorsTableNode.AddColumn()
      column.SetName(self.usFiducialsNode.GetNthFiducialLabel(index)[13:])
      import math
      threeDDist = math.sqrt((usPos[0]-mrPos[0])**2 + (usPos[1]-mrPos[1])**2 + (usPos[2]-mrPos[2])**2)
      column.SetValue(0, str( threeDDist ))
      column.SetValue(1, str( abs(usPos[0]-mrPos[0]) ))
      column.SetValue(2, str( abs(usPos[1]-mrPos[1]) ))
      column.SetValue(3, str( abs(usPos[2]-mrPos[2]) ))

    return True

#
# -----------------------------------------------------------------------------
# ProstateMRIUSContourPropagationTest
# -----------------------------------------------------------------------------
#

class ProstateMRIUSContourPropagationTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  """

  #------------------------------------------------------------------------------
  def test_ProstateMRIUSContourPropagation_FullTest(self):
    try:
      # Check for modules
      self.assertIsNotNone( slicer.modules.dicomrtimportexport )
      self.assertIsNotNone( slicer.modules.subjecthierarchy )
      self.assertIsNotNone( slicer.modules.segmentations )
      self.assertIsNotNone( slicer.modules.brainsfit )
      self.assertIsNotNone( slicer.modules.distancemapbasedregistration )
      self.assertIsNotNone( slicer.modules.cropvolume )

      self.TestSection_00_SetupPathsAndNames()
      self.TestSection_01A_OpenTempDatabase()
      self.TestSection_01B_DownloadData()
      self.TestSection_01C_ImportStudy()
      self.TestSection_01D_SelectLoadablesAndLoad()
      self.TestSection_02_PerformRegistration()
      self.TestSection_03_CalculateSimilarity()
      self.TestUtility_ClearDatabase()

    except Exception as e:
      logging.error('Exception happened! Details:')
      import traceback
      traceback.print_exc()
      pass

  #------------------------------------------------------------------------------
  def TestSection_00_SetupPathsAndNames(self):
    prostateMRIUSContourPropagationDir = slicer.app.temporaryPath + '/ProstateMRIUSContourPropagation'
    if not os.access(prostateMRIUSContourPropagationDir, os.F_OK):
      os.mkdir(prostateMRIUSContourPropagationDir)

    self.dicomDataDir = prostateMRIUSContourPropagationDir + '/MRIUSFusionPatient4Dicom'
    if not os.access(self.dicomDataDir, os.F_OK):
      os.mkdir(self.dicomDataDir)

    self.dicomDatabaseDir = prostateMRIUSContourPropagationDir + '/CtkDicomDatabase'
    self.dicomZipFilePath = prostateMRIUSContourPropagationDir + '/MRIUSFusionPatient4.zip'
    self.expectedNumOfFilesInDicomDataDir = 251
    self.tempDir = prostateMRIUSContourPropagationDir + '/Temp'

    self.patientName = '0PHYSIQUE^F_MRI_US_4 (PHYEP004)'
    self.usSegmentationName = '1: RTSTRUCT: OCP RTS v4.2.21'
    self.usProstateSegmentName = 'target'
    self.usVolumeName = '1: Oncentra Prostate Image Series'
    self.mrSegmentationName = '9: RTSTRUCT: Prostate'
    self.mrProstateSegmentName = 'Prostate'
    self.mrVolumeName = '4: T2 SPACE RST TRA ISO 3D'

    self.setupPathsAndNamesDone = True

  #------------------------------------------------------------------------------
  def TestSection_01A_OpenTempDatabase(self):
    # Open test database and empty it
    try:
      if not os.access(self.dicomDatabaseDir, os.F_OK):
        os.mkdir(self.dicomDatabaseDir)

      if slicer.dicomDatabase:
        self.originalDatabaseDirectory = os.path.split(slicer.dicomDatabase.databaseFilename)[0]
      else:
        self.originalDatabaseDirectory = None
        settings = qt.QSettings()
        settings.setValue('DatabaseDirectory', self.dicomDatabaseDir)

      dicomWidget = slicer.modules.dicom.widgetRepresentation().self()
      dicomWidget.onDatabaseDirectoryChanged(self.dicomDatabaseDir)
      self.assertTrue( slicer.dicomDatabase.isOpen )
      slicer.dicomDatabase.initializeDatabase()

    except Exception as e:
      import traceback
      traceback.print_exc()
      self.delayDisplay('Test caused exception!\n' + str(e),self.delayMs*2)
      raise Exception("Exception occurred, handled, thrown further to workflow level")

  #------------------------------------------------------------------------------
  def TestSection_01B_DownloadData(self):
    try:
      import urllib
      downloads = (
          ('http://slicer.kitware.com/midas3/download/item/318330/MRIUSFusionPatient4.zip', self.dicomZipFilePath),
          )

      downloaded = 0
      for url,filePath in downloads:
        if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
          if downloaded == 0:
            self.delayDisplay('Downloading input data to folder\n' + self.dicomZipFilePath + '.\n\n  It may take a few minutes...',self.delayMs)
          logging.info('Requesting download from %s...' % (url))
          urllib.urlretrieve(url, filePath)
          downloaded += 1
        else:
          self.delayDisplay('Input data has been found in folder ' + self.dicomZipFilePath, self.delayMs)
      if downloaded > 0:
        self.delayDisplay('Downloading input data finished',self.delayMs)

      numOfFilesInDicomDataDir = len([file for folderList in [files for root, subdirs, files in os.walk(self.dicomDataDir)] for file in folderList])
      if (numOfFilesInDicomDataDir != self.expectedNumOfFilesInDicomDataDir):
        slicer.app.applicationLogic().Unzip(self.dicomZipFilePath, self.dicomDataDir)
        self.delayDisplay("Unzipping done",self.delayMs)

      numOfFilesInDicomDataDirTest = len([file for folderList in [files for root, subdirs, files in os.walk(self.dicomDataDir)] for file in folderList])
      self.assertEqual( numOfFilesInDicomDataDirTest, self.expectedNumOfFilesInDicomDataDir )

    except Exception as e:
      import traceback
      traceback.print_exc()
      self.delayDisplay('Test caused exception!\n' + str(e),self.delayMs*2)
      raise Exception("Exception occurred, handled, thrown further to workflow level")

  #------------------------------------------------------------------------------
  def TestSection_01C_ImportStudy(self):
    self.delayDisplay("Import Day 1 study",self.delayMs)

    try:
      slicer.util.selectModule('DICOM')

      # Import study to database
      dicomWidget = slicer.modules.dicom.widgetRepresentation().self()
      indexer = ctk.ctkDICOMIndexer()
      self.assertIsNotNone( indexer )

      indexer.addDirectory( slicer.dicomDatabase, self.dicomDataDir )

      self.assertEqual( len(slicer.dicomDatabase.patients()), 1 )
      self.assertIsNotNone( slicer.dicomDatabase.patients()[0] )

    except Exception as e:
      import traceback
      traceback.print_exc()
      self.delayDisplay('Test caused exception!\n' + str(e),self.delayMs*2)
      raise Exception("Exception occurred, handled, thrown further to workflow level")

  #------------------------------------------------------------------------------
  def TestSection_01D_SelectLoadablesAndLoad(self):
    self.delayDisplay("Select loadables and load data",self.delayMs)

    try:
      numOfScalarVolumeNodesBeforeLoad = len( slicer.util.getNodes('vtkMRMLScalarVolumeNode*') )
      numOfSegmentationNodesBeforeLoad = len( slicer.util.getNodes('vtkMRMLSegmentationNode*') )

      # Choose first patient from the patient list
      dicomWidget = slicer.modules.dicom.widgetRepresentation().self()
      self.delayDisplay("Wait for DICOM browser to initialize",self.delayMs)
      patient = slicer.dicomDatabase.patients()[0]
      studies = slicer.dicomDatabase.studiesForPatient(patient)
      series = [slicer.dicomDatabase.seriesForStudy(study) for study in studies]
      seriesUIDs = [uid for uidList in series for uid in uidList]
      dicomWidget.detailsPopup.offerLoadables(seriesUIDs, 'SeriesUIDList')
      dicomWidget.detailsPopup.examineForLoading()

      # Make sure the loadables are good (RT is assigned to 2 out of 4 and they are selected)
      loadablesByPlugin = dicomWidget.detailsPopup.loadablesByPlugin
      rtFound = False
      loadablesForRt = 0
      for plugin in loadablesByPlugin:
        if plugin.loadType == 'RT':
          rtFound = True
        else:
          continue
        for loadable in loadablesByPlugin[plugin]:
          loadablesForRt += 1
          self.assertTrue( loadable.selected )

      self.assertTrue( rtFound )
      self.assertEqual( loadablesForRt, 2 )

      dicomWidget.detailsPopup.loadCheckedLoadables()

      # Verify that the correct number of objects were loaded
      self.assertEqual( len( slicer.util.getNodes('vtkMRMLScalarVolumeNode*') ), numOfScalarVolumeNodesBeforeLoad + 2 )
      self.assertEqual( len( slicer.util.getNodes('vtkMRMLSegmentationNode*') ), numOfSegmentationNodesBeforeLoad + 2 )

    except Exception as e:
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
      slicer.util.selectModule('ProstateMRIUSContourPropagation')
      moduleWidget = slicer.modules.prostatemriuscontourpropagation.widgetRepresentation().self()
      moduleWidget.selectInitialPatients()

      # Check patient selections
      self.assertEqual(moduleWidget.usPatientItemCombobox.currentItem(), patientShItemID)
      self.assertEqual(moduleWidget.mrPatientItemCombobox.currentItem(), patientShItemID)

      # Check volume selections
      self.assertIsNotNone(moduleWidget.usVolumeNodeCombobox.currentNode())
      self.assertEqual(moduleWidget.usVolumeNodeCombobox.currentNode().GetName(), self.usVolumeName)
      self.assertIsNotNone(moduleWidget.mrVolumeNodeCombobox.currentNode())
      self.assertEqual(moduleWidget.mrVolumeNodeCombobox.currentNode().GetName(), self.mrVolumeName)

      # Set US segmentation and segment (it needs to be manually changed for this dataset)
      usSegmentationNode = slicer.util.getNode(self.usSegmentationName)
      self.assertIsNotNone(usSegmentationNode)
      moduleWidget.usSegmentationNodeCombobox.setCurrentNode(usSegmentationNode)
      moduleWidget.usProstateSegmentNameCombobox.setCurrentIndex( moduleWidget.usProstateSegmentNameCombobox.findText(self.usProstateSegmentName) )
      self.assertEqual(moduleWidget.usProstateSegmentNameCombobox.currentText, self.usProstateSegmentName)

      # Set US segmentation
      mrSegmentationNode = slicer.util.getNode(self.mrSegmentationName)
      self.assertIsNotNone(mrSegmentationNode)
      moduleWidget.mrSegmentationNodeCombobox.setCurrentNode(mrSegmentationNode)
      self.assertEqual(moduleWidget.mrProstateSegmentNameCombobox.currentText, self.mrProstateSegmentName)

      # Perform registration
      qt.QApplication.setOverrideCursor(qt.QCursor(qt.Qt.BusyCursor))
      success = moduleWidget.logic.performRegistration()
      qt.QApplication.restoreOverrideCursor()
      self.assertTrue(success)

      # Check transforms
      preAlignmentTransformNode = slicer.util.getNode('PreAlignmentMri2UsLinearTransform')
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

    except Exception as e:
      import traceback
      traceback.print_exc()
      self.delayDisplay('Test caused exception!\n' + str(e),self.delayMs*2)
      raise Exception("Exception occurred, handled, thrown further to workflow level")

  #------------------------------------------------------------------------------
  def TestSection_03_CalculateSimilarity(self):
    self.delayDisplay("Calculate similarity",self.delayMs)

    try:
      moduleWidget = slicer.modules.prostatemriuscontourpropagation.widgetRepresentation().self()
      moduleWidget.onCalculateSegmentSimilarity()

      layoutManager = slicer.app.layoutManager()
      self.assertEqual(layoutManager.layout, slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpTableView)

      # Check Dice metrics
      # Note: Allow some deviation, because the purpose of the test is to make sure the values make sense,
      #  and comparison was successful, instead of ensuring the registration result is exactly the same
      # Note: First four rows contain the names of the compared segmentation nodes and segments
      self.assertIsNotNone(moduleWidget.logic.diceTableNode)
      diceTable = moduleWidget.logic.diceTableNode.GetTable()
      self.assertIsNotNone(diceTable)
      self.assertGreater(diceTable.GetValue( 4,1).ToDouble(), 0.9)
      self.assertGreater(diceTable.GetValue( 5,1).ToDouble(), 25)
      self.assertLess(diceTable.GetValue( 6,1).ToDouble(), 75)
      self.assertLess(diceTable.GetValue( 7,1).ToDouble(), 2)
      self.assertLess(diceTable.GetValue( 8,1).ToDouble(), 1.5)
      self.assertAlmostEqual(diceTable.GetValue(11,1).ToDouble() / 2, 29.5, 0)
      self.assertAlmostEqual(diceTable.GetValue(12,1).ToDouble() / 2, 29.5, 0)
      # self.assertEqual(diceTable.GetValue( 9,1).ToString(), '(-1.05024, 33.1222, -34.9534)')
      # self.assertEqual(diceTable.GetValue(10,1).ToString(), '(-0.960999, 33.0069, -34.9166)')

      # Check Hausdorff metrics (allow maximum 1% deviation)
      # (first four rows contain the names of the compared segmentation nodes and segments)
      self.assertIsNotNone(moduleWidget.logic.hausdorffTableNode)
      hausdorffTable = moduleWidget.logic.hausdorffTableNode.GetTable()
      self.assertIsNotNone(hausdorffTable)
      self.assertLess(hausdorffTable.GetValue(4,1).ToDouble(), 5)
      self.assertLess(hausdorffTable.GetValue(5,1).ToDouble(), 1)
      self.assertLess(hausdorffTable.GetValue(6,1).ToDouble(), 2.5)

    except Exception as e:
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

    self.moduleName = "ProstateMRIUSContourPropagation"

  #------------------------------------------------------------------------------
  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()

    self.test_ProstateMRIUSContourPropagation_FullTest()

  #------------------------------------------------------------------------------
  # Utility functions
  #------------------------------------------------------------------------------
  def TestUtility_ClearDatabase(self):
    self.delayDisplay("Clear database",self.delayMs)

    slicer.dicomDatabase.initializeDatabase()
    slicer.dicomDatabase.closeDatabase()
    self.assertFalse( slicer.dicomDatabase.isOpen )

    self.delayDisplay("Restoring original database directory",self.delayMs)
    if self.originalDatabaseDirectory:
      dicomWidget = slicer.modules.dicom.widgetRepresentation().self()
      dicomWidget.onDatabaseDirectoryChanged(self.originalDatabaseDirectory)
