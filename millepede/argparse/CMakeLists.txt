cmake_minimum_required(VERSION 3.12.4)

# 判断是否为顶层项目
if(NOT DEFINED PROJECT_NAME)
  set(ARGPARSE_IS_TOP_LEVEL ON)
else()
  set(ARGPARSE_IS_TOP_LEVEL OFF)
endif()
project(argparse
        VERSION 3.2.0 
        DESCRIPTION "A single header argument parser for C++17"
        HOMEPAGE_URL "https://github.com/p-ranav/argparse"
        LANGUAGES CXX
)
# 在非顶层项目中，禁止安装、测试和示例
option(ARGPARSE_INSTALL "Include an install target" ${ARGPARSE_IS_TOP_LEVEL})
option(ARGPARSE_BUILD_TESTS "Build tests" ${ARGPARSE_IS_TOP_LEVEL})
option(ARGPARSE_BUILD_SAMPLES "Build samples" OFF)

# 安装时会用到这两个 CMake 模块提供的变量和函数
include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

# 上面的 INTERFACE 指的是库本身，下面两个指库内的属性为 INTERFACE
# 创建 argparse 为 INTERFACE (header-only) 库
add_library(argparse INTERFACE)
add_library(argparse::argparse ALIAS argparse)
# 给 argparse 库添加属性，属性的作用范围设置为 INTERFACE，传播给所有使用者
target_compile_features(argparse INTERFACE cxx_std_17)
target_include_directories(argparse INTERFACE
# 根据场景不同，提供不同的头文件路径
  $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
  $<BUILD_INTERFACE:${CMAKE_CURRENT_LIST_DIR}/include>)

# 添加测试和示例子模块，非顶层项目中禁用
if(ARGPARSE_BUILD_SAMPLES)
  add_subdirectory(samples)
endif()
if(ARGPARSE_BUILD_TESTS)
  add_subdirectory(test)
endif()

# 安装配置，非顶层项目中禁用
if(ARGPARSE_INSTALL)
  install(TARGETS argparse EXPORT argparseConfig)
  install(EXPORT argparseConfig
          NAMESPACE argparse::
          DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME})
  install(FILES ${CMAKE_CURRENT_LIST_DIR}/include/argparse/argparse.hpp
          DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/argparse)


  set(CONFIG_FILE_NAME_WITHOUT_EXT "${PROJECT_NAME}Config")
  set(CMAKE_CONFIG_FILE_BASENAME "${CMAKE_CURRENT_BINARY_DIR}/${CONFIG_FILE_NAME_WITHOUT_EXT}")
  set(CMAKE_CONFIG_VERSION_FILE_NAME "${CMAKE_CONFIG_FILE_BASENAME}-version.cmake")
  set(CMAKE_CONFIG_FILE_NAME "${CMAKE_CONFIG_FILE_BASENAME}.cmake")

  if(${CMAKE_VERSION} VERSION_GREATER "3.14")
  	set(OPTIONAL_ARCH_INDEPENDENT "ARCH_INDEPENDENT")
  endif()

  write_basic_package_version_file("${CMAKE_CONFIG_VERSION_FILE_NAME}"
      COMPATIBILITY SameMajorVersion
      ${OPTIONAL_ARCH_INDEPENDENT}
  )

  export(EXPORT argparseConfig
         NAMESPACE argparse::)

  install(FILES "${CMAKE_CONFIG_VERSION_FILE_NAME}"
         DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME}")

  set(PackagingTemplatesDir "${CMAKE_CURRENT_SOURCE_DIR}/packaging")

  set(CPACK_PACKAGE_NAME "${PROJECT_NAME}")
  set(CPACK_PACKAGE_VENDOR "argparse (C++) developers")
  set(CPACK_PACKAGE_DESCRIPTION "${PROJECT_DESCRIPTION}")
  set(CPACK_DEBIAN_PACKAGE_NAME "${CPACK_PACKAGE_NAME}")
  set(CPACK_RPM_PACKAGE_NAME "${CPACK_PACKAGE_NAME}")
  set(CPACK_PACKAGE_HOMEPAGE_URL "${PROJECT_HOMEPAGE_URL}")
  set(CPACK_PACKAGE_MAINTAINER "Pranav Srinivas Kumar")
  set(CPACK_DEBIAN_PACKAGE_MAINTAINER "${CPACK_PACKAGE_MAINTAINER}")
  set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE")
  set(CPACK_RESOURCE_FILE_README "${CMAKE_CURRENT_SOURCE_DIR}/README.md")

  set(CPACK_DEBIAN_PACKAGE_NAME "lib${PROJECT_NAME}-dev")
  set(CPACK_DEBIAN_PACKAGE_DEPENDS "libc6-dev")
  set(CPACK_DEBIAN_PACKAGE_SUGGESTS "cmake, pkg-config, pkg-conf")

  set(CPACK_RPM_PACKAGE_NAME "lib${PROJECT_NAME}-devel")
  set(CPACK_RPM_PACKAGE_SUGGESTS "${CPACK_DEBIAN_PACKAGE_SUGGESTS}")

  set(CPACK_DEB_COMPONENT_INSTALL ON)
  set(CPACK_RPM_COMPONENT_INSTALL ON)
  set(CPACK_NSIS_COMPONENT_INSTALL ON)
  set(CPACK_DEBIAN_COMPRESSION_TYPE "xz")

  set(PKG_CONFIG_FILE_NAME "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.pc")
  configure_file("${PackagingTemplatesDir}/pkgconfig.pc.in" "${PKG_CONFIG_FILE_NAME}" @ONLY)
  install(FILES "${PKG_CONFIG_FILE_NAME}"
        DESTINATION "${CMAKE_INSTALL_LIBDIR}/pkgconfig"
  )
endif()

# 用于创建软件安装包，非安装模式无效
include(CPack)
