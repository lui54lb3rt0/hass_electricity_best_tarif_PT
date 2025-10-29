# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.0] - 2025-10-08

### 🚀 Major Features
- **Energy type selection**: Users can now choose between electricity only (ELE), gas only (GN), dual offers (ELE+GN), or all types during setup
- **Enhanced filtering**: Improved energy type filtering logic to support gas natural and dual offers
- **Flexible configuration**: New configuration option allows users to access previously filtered out dual electricity+gas packages

### ✨ Enhancements
- **Backward compatibility**: Existing installations default to electricity-only filtering to maintain current behavior
- **Enhanced logging**: Added energy type information to debug logs and coordinator status
- **Improved config flow**: Two-step configuration with energy type selection before offer code fetching
- **Dynamic offer codes**: Offer codes are now fetched based on selected energy type for better accuracy

### 🔧 Technical Improvements
- **Config flow enhancement**: Updated to collect energy type preference during initial setup
- **Data loader updates**: Enhanced `async_process_csv` function to support all energy type filtering modes
- **Coordinator updates**: Extended coordinator to handle energy type parameter throughout the data pipeline
- **Constants addition**: Added `ENERGY_TYPE_OPTIONS` for consistent energy type handling

### 📚 Configuration Options
- **Eletricidade apenas**: Traditional electricity-only offers (default for backward compatibility)
- **Gás Natural apenas**: Gas-only offers for users with gas-only needs
- **Eletricidade e Gás Natural**: Dual offers combining both electricity and gas services
- **Todos os tipos**: All available offers regardless of energy type

### 🔄 Migration Notes
- **Existing users**: No action required - will continue using electricity-only filtering
- **New installations**: Can choose preferred energy type during setup
- **Reconfiguration**: Remove and re-add integration to change energy type preference

## [2.4.0] - 2025-10-07

### 🚀 Major Features
- **Comprehensive README revamp**: Professional documentation with badges, detailed installation guides, and extensive examples
- **Enhanced troubleshooting**: Complete FAQ section with common problems and solutions
- **Advanced template examples**: Ready-to-use YAML snippets for tariff comparison and automation
- **Project roadmap**: Clear feature timeline and contribution guidelines

### ✨ Enhancements
- **Professional branding**: Integration now shows logo and proper versioning in Home Assistant UI
- **Image optimization**: Logo and icon files optimized for Home Assistant brands repository submission
- **Documentation structure**: Comprehensive sections covering installation, configuration, usage, and troubleshooting
- **Template gallery**: Advanced examples for price comparison, automation triggers, and notifications

### 🔧 Technical Improvements
- **Manifest.json optimization**: Removed invalid logo/icon URLs as per Home Assistant standards
- **Version consistency**: Dynamic version loading from manifest.json for accurate display
- **Brands repository preparation**: Created submission scripts and guides for official logo display
- **Code organization**: Better separation of concerns and improved maintainability

### 📚 Documentation
- **Installation methods**: Both HACS and manual installation with detailed steps
- **Configuration examples**: Complete setup scenarios with real-world use cases
- **API reference**: Comprehensive attribute documentation and template usage
- **Troubleshooting guide**: Solutions for common issues with diagnostic tools
- **Contributing guidelines**: Clear instructions for community contributions

### 🐛 Bug Fixes
- **Manifest format**: Corrected logo/icon handling according to Home Assistant specifications
- **Version display**: Fixed version showing as commit ID instead of semantic version
- **Documentation links**: Updated all references to current repository structure

### 📦 Assets
- **Logo optimization**: 256x225 interlaced PNG for professional appearance
- **Icon standardization**: 256x256 interlaced PNG meeting Home Assistant requirements
- **Submission scripts**: Automated tools for Home Assistant brands repository submission

## [2.3.3] - 2025-10-07

### 🔧 Technical Updates
- **Image processing**: Added ImageMagick optimization for logo and icon files
- **Git management**: Enhanced version control with proper tagging system
- **Submission preparation**: Created tools for Home Assistant brands repository submission

## [2.3.2] - 2025-10-07

### 🖼️ Visual Improvements
- **Logo integration**: Added official integration logo for Home Assistant UI
- **Icon support**: Created matching icon for entity displays
- **Branding consistency**: Unified visual identity across all components

## [2.3.1] - 2025-10-07
### 🐛 Fixes
- **Blocking I/O operations**: Resolved async/sync conflicts in downloader debug mode
- **Data quality improvements**: Better handling of empty/NaN values with context-aware defaults
- **Entity deduplication**: Fixed multiple entities per tariff by implementing offer-based grouping
- **Unique ID generation**: Enhanced algorithm to prevent sensor duplication issues

### ✨ Features
- **Smart data cleaning**: Context-aware display formatting for different field types
- **Robust URL discovery**: Multiple HTML parsing strategies with BeautifulSoup4 integration
- **Dynamic versioning**: Automatic version management from manifest.json
- **Enhanced logging**: Improved error handling and diagnostic information

### 🔄 Changes
- **Sensor consolidation**: One entity per offer with aggregated billing cycle data
- **Dependency updates**: Added BeautifulSoup4 requirement for better HTML parsing
- **ID simplification**: Streamlined unique ID generation for better maintainability

## [2.2.1] - 2025-09-22

### 🎨 Visual Enhancements
- **Integration logo**: Added official logo support for professional appearance
- **Documentation improvements**: Enhanced README with better examples and troubleshooting

## [2.2.0] - 2025-09-22

### 🔄 Automation Features
- **Automatic scheduling**: Daily refresh at 11:00 AM local time
- **Background updates**: Non-blocking data synchronization with ERSE servers
- **Memory optimization**: Improved callback management and cleanup processes
- **Fresh data guarantee**: Automatic sensor updates with latest CSV data

## [2.0.1] - 2025-09-22

### 🐛 Critical Fixes
- **Timestamp handling**: Fixed device_class=timestamp using native datetime objects
- **State consistency**: Improved sensor state management and reliability

## [2.0.0] - 2025-09-22

### 🚀 Major Architecture Overhaul
- **Async pipeline**: Complete migration to aiohttp with async/await patterns  
- **Non-blocking operations**: Eliminated synchronous requests that blocked event loop
- **Enhanced sensor attributes**: All CSV columns exposed as normalized entity attributes
- **Timestamp states**: Sensors now use proper timestamp device class with ISO8601 format
- **Debug capabilities**: Comprehensive logging for data inspection and troubleshooting
- **Manifest updates**: Added iot_class and integration_type specifications

## [1.5.0] - 2025-09-17

### 🔧 Integration Stability
- **Config flow enhancement**: Added `async_setup_entry` to support proper config flow setup
- **Setup error resolution**: Fixed integration initialization and entry creation issues

### 📈 Version Management
- **Semantic versioning**: Incremented to version 1.5.0 with proper changelog maintenance

## [1.4.0] - 2025-09-17

### 🎯 User Experience
- **Config flow completion**: Fixed entry creation after power selection allowing successful setup
- **Setup reliability**: Improved configuration flow stability and error handling

### 📈 Version Management  
- **Version increment**: Updated to 1.4.0 reflecting UX improvements

## [1.3.0] - 2025-09-17

### ✨ UI Enhancements
- **Power selector**: Added dropdown for "Potência contratada" during integration setup
- **User guidance**: Improved setup flow with intuitive power selection interface

### 📈 Version Management
- **Version update**: Incremented to 1.3.0 for new UI features

## [1.2.0] - 2025-09-17

### 📚 Documentation Overhaul
- **Setup clarification**: Updated README to emphasize Integrations UI over configuration.yaml
- **Installation guide**: Improved step-by-step instructions for better user experience
- **Minor corrections**: Fixed various documentation inconsistencies

## [1.1.0] - 2025-09-17

### 🔧 Compatibility Improvements
- **Import fixes**: Corrected SensorEntity import for Home Assistant compatibility
- **Module integration**: Enhanced DataFrame loading via data_loader for cleaner setup

## [1.0.0] - 2025-09-17

### 🎉 Initial Release
- **ERSE data integration**: Automatic download and processing of official Portuguese electricity tariff data
- **Data joining**: Intelligent merge of commercial conditions and price tables
- **Smart filtering**: Filter offers by contracted power (Pot_Cont) with automatic data cleanup
- **Gas exclusion**: Automatic removal of natural gas (GN) related columns and offers
- **Dynamic sensors**: One sensor entity per offer (CODProposta) with complete tariff details
- **Rich attributes**: All offer conditions exposed as entity attributes for advanced automation
- **Tariff comparison**: Enable side-by-side comparison and selection in Home Assistant
- **Professional foundation**: Solid architecture for future enhancements and community contributions

---

## 📋 Version History Summary

- **v2.4.0**: Major documentation revamp, professional branding, and submission preparation
- **v2.3.x**: Logo integration, image optimization, and visual improvements  
- **v2.2.x**: Automatic scheduling and background updates
- **v2.1.x**: Timestamp handling and state management fixes
- **v2.0.x**: Complete async architecture overhaul
- **v1.x.x**: Foundation, UI improvements, and initial release

For detailed technical information about each release, see the individual version sections above.
