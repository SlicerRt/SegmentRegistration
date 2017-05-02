cmake_minimum_required(VERSION 2.8.9)

#-----------------------------------------------------------------------------
set(EXTENSION_NAME SegmentRegistration)

# ------------------------------------------------------------------------
set(SEGMENTREGISTRATION_VERSION_MAJOR "1")
set(SEGMENTREGISTRATION_VERSION_MINOR "0")
set(SEGMENTREGISTRATION_VERSION_PATCH "0")
set(SEGMENTREGISTRATION_VERSION ${SEGMENTREGISTRATION_VERSION_MAJOR}.${SEGMENTREGISTRATION_VERSION_MINOR}.${SEGMENTREGISTRATION_VERSION_PATCH})

#-----------------------------------------------------------------------------
set(EXTENSION_HOMEPAGE "")
set(EXTENSION_CATEGORY "Registration")
set(EXTENSION_CONTRIBUTORS "Csaba Pinter (PerkLab, Queen's University)")
set(EXTENSION_DESCRIPTION "Segment registration is an extension that contains generic and more specialized modules for registering two delineations of the same structure, and propagating other segmented structures from one dataset to the other (also called fusion or contour propagation).")
set(EXTENSION_ICONURL "")
set(EXTENSION_SCREENSHOTURLS "")
set(EXTENSION_DEPENDS "SlicerProstate SlicerRT")

#-----------------------------------------------------------------------------
find_package(Slicer COMPONENTS ConfigurePrerequisites REQUIRED)
project(SegmentRegistration)
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
add_subdirectory(ProstateMRIUSContourPropagation)
add_subdirectory(SegmentRegistration)

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
