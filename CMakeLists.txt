
file(GLOB_RECURSE PYSRC "*.py")
source_group(python FILES ${PYSRC}) 

foreach(pyfile ${PYSRC})
 #message("${pyfile}") 
 STRING(REGEX REPLACE ${CMAKE_SOURCE_DIR}/src/python/ "" out_file ${pyfile})
 #message("${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/${out_file}")
  ADD_CUSTOM_COMMAND(OUTPUT "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/${out_file}" 
    COMMAND ${CMAKE_COMMAND} -E copy "${pyfile}" 
    "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/${out_file}" 
    DEPENDS   "${pyfile}" 
    ) 
   list(APPEND pyfile_dest "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/${out_file}")   
endforeach(pyfile) 

ADD_CUSTOM_TARGET(CopyPython ALL DEPENDS ${pyfile_dest}) 

INSTALL(DIRECTORY ${CMAKE_SOURCE_DIR}/src/python/ DESTINATION bin )

#configure_file(${CMAKE_SOURCE_DIR}/src/python/zui/images/genprefs.png ${CMAKE_CURRENT_BINARY_DIR}/zui/images/genprefs.png COPYONLY)