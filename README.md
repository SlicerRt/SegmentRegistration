# Segment Registration
![Logo](Logo/SegmentRegistration_Logo_128.png)

3D Slicer extension for segment registration (aka fusion, contour propagation).

As the registration step uses the Distance Map Based Registration module, please cite this paper if you use this extension:
Fedorov, A., Khallaghi, S., Sánchez, C. A., Lasso, A., Fels, S., Tuncali, K., ... & Nguyen, P. L. (2015). Open-source image registration for MRI–TRUS fusion-guided prostate interventions. International journal of computer assisted radiology and surgery, 10(6), 925-934.

Paper to cite if you use the Prostate MRI-US Contour Propagation module:
Poulin, E., Boudam, K., Pinter, C., Kadoury, S., Lasso, A., Fichtinger, G., & Ménard, C. (2017). Validation of MRI to US Registration for Focal HDR Prostate Brachytherapy. Brachytherapy, 16(3), S56-S57.

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
