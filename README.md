# Segment Registration
![Logo](Logo/SegmentRegistration_Logo_128.png)

3D Slicer extension for segment registration (aka fusion, contour propagation)

## Modules

### Segment Registration

Generic module to register corresponding segments in two segmentations

### Prostate MRI-US Contour Propagation

Specialized module to register prostate contours in an MRI and an ultrasound study. Extra features:
* If input is DICOM, then selections are automatically initialized
* Calculate Dice similarity metrics and Hausdorff distances
* Calculate TRE with fiducials
* Export deformed MRI contours and image to DICOM, so that it can be imported to commercial system for brachytherapy cathether insertion

![Screenshot](https://www.slicer.org/w/images/a/a1/20170526_ProstatMRIUSContourPropagation.png)
