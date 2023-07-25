cmake_minimum_required(VERSION 2.8.9)

#-----------------------------------------------------------------------------
set(EXTENSION_NAME SegmentRegistration)

# ------------------------------------------------------------------------
set(SEGMENTREGISTRATION_VERSION_MAJOR "1")
set(SEGMENTREGISTRATION_VERSION_MINOR "0")
set(SEGMENTREGISTRATION_VERSION_PATCH "0")
set(SEGMENTREGISTRATION_VERSION ${SEGMENTREGISTRATION_VERSION_MAJOR}.${SEGMENTREGISTRATION_VERSION_MINOR}.${SEGMENTREGISTRATION_VERSION_PATCH})

#-----------------------------------------------------------------------------
set(EXTENSION_HOMEPAGE "https://github.com/SlicerRt/SegmentRegistration")
set(EXTENSION_CATEGORY "Registration")
set(EXTENSION_CONTRIBUTORS "Csaba Pinter (PerkLab, Queen's University)")
set(EXTENSION_DESCRIPTION "Segment registration is an extension that contains generic and more specialized modules for registering two delineations of the same structure, and propagating other segmented structures from one dataset to the other (also called fusion or contour propagation).")
set(EXTENSION_ICONURL "https://github.com/SlicerRt/SegmentRegistration/raw/master/Logo/SegmentRegistration_Logo_128.png")
set(EXTENSION_SCREENSHOTURLS "https://www.slicer.org/w/images/a/a1/20170526_ProstatMRIUSContourPropagation.png https://www.slicer.org/w/images/1/15/20160329_MRIUS_1500.gif")
set(EXTENSION_DEPENDS SlicerProstate SlicerRT)

#-----------------------------------------------------------------------------
find_package(Slicer COMPONENTS ConfigurePrerequisites REQUIRED)
project(SegmentRegistration)
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

if (NOT DEFINED Slicer_EXTENSION_SOURCE_DIRS)
  find_package(SlicerProstate REQUIRED)
  find_package(SlicerRT REQUIRED)
else()
  # Allow usage if dependent extension is bundled
endif()

set(DEPENDENCY_BUILD_DIRS "")
if(CMAKE_CONFIGURATION_TYPES)
  foreach(config ${CMAKE_CONFIGURATION_TYPES})
    list(APPEND DEPENDENCY_BUILD_DIRS "${SlicerProstate_DIR}/${Slicer_QTLOADABLEMODULES_LIB_DIR}/${config}")
    list(APPEND DEPENDENCY_BUILD_DIRS "${SlicerProstate_DIR}/${Slicer_CLIMODULES_LIB_DIR}/${config}")
    list(APPEND DEPENDENCY_BUILD_DIRS "${SlicerRT_DIR}/${Slicer_QTLOADABLEMODULES_LIB_DIR}/${config}")
    list(APPEND DEPENDENCY_BUILD_DIRS "${SlicerRT_DIR}/${Slicer_CLIMODULES_LIB_DIR}/${config}")
  endforeach()
else()
  set(DEPENDENCY_BUILD_DIRS "${SlicerProstate_DIR}/${Slicer_QTLOADABLEMODULES_LIB_DIR}")
  set(DEPENDENCY_BUILD_DIRS "${SlicerProstate_DIR}/${Slicer_CLIMODULES_LIB_DIR}")
  set(DEPENDENCY_BUILD_DIRS "${SlicerRT_DIR}/${Slicer_QTLOADABLEMODULES_LIB_DIR}")
  set(DEPENDENCY_BUILD_DIRS "${SlicerRT_DIR}/${Slicer_CLIMODULES_LIB_DIR}")
endif()

# message("DEPENDENCY_BUILD_DIRS: ${DEPENDENCY_BUILD_DIRS}")
set(DEPENDENCIES_ADDITIONAL_MODULE_PATHS
  ${DEPENDENCY_BUILD_DIRS}
  ${SlicerProstate_DIR}/${Slicer_QTSCRIPTEDMODULES_LIB_DIR}
  ${SlicerRT_DIR}/${Slicer_QTSCRIPTEDMODULES_LIB_DIR}
  )

#-----------------------------------------------------------------------------
add_subdirectory(ProstateMRIUSContourPropagation)
add_subdirectory(SegmentRegistration)

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
