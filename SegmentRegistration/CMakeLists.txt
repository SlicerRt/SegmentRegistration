cmake_minimum_required(VERSION 2.8.9)

#-----------------------------------------------------------------------------
set(MODULE_NAME SegmentRegistration)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}
  )

set(MODULE_PYTHON_RESOURCES
  # Resources/Icons/${MODULE_NAME}.png
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  # WITH_GENERIC_TESTS #TODO: It fails because the generic test does not seem to add the module paths
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)
  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(
    SCRIPT ${MODULE_NAME}.py
    SLICER_ARGS --additional-module-paths
      ${CMAKE_BINARY_DIR}/${Slicer_QTSCRIPTEDMODULES_LIB_DIR}
      ${DEPENDENCIES_ADDITIONAL_MODULE_PATHS}
    )
  # These additional module paths are needed because they are not otherwise found correctly

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
