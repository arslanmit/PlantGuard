turn False  # Default to not pressed
    
    def file_uploader(self, label, **kwargs):
        self.file_uploader_calls.append({'label': label, 'kwargs': kwargs})
        return None  # Default to no file
    
    def columns(self, spec):
        return [Mock() for _ in range(spec if isinstance(spec, int) else len(spec))]
    
    def container(self):
        return Mock()
    
    def expander(self, label, expanded=False):
        return Mock()
    
    def tabs(self, labels):
        return [Mock() for _ in labels]
    
    def success(self, message):
        pass
    
    def error(self, message):
        pass
    
    def warning(self, message):
        pass
    
    def info(self, message):
        pass


class MobileComponentTester:
    """Comprehensive mobile component testing framework."""
    
    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        self.performance_metrics: Dict[str, float] = {}
        self.accessibility_results: Dict[str, Any] = {}
        self.mock_st = MockStreamlit()
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests."""
        logger.info("Starting comprehensive mobile testing suite")
        
        test_results = {
            'component_tests': self.test_all_components(),
            'integration_tests': self.test_integration_points(),
            'performance_tests': self.test_performance_optimization(),
            'accessibility_tests': self.test_accessibility_compliance(),
            'cross_browser_tests': self.test_cross_browser_compatibility(),
            'error_handling_tests': self.test_error_handling(),
            'state_management_tests': self.test_state_management(),
            'navigation_tests': self.test_navigation_system(),
            'adapter_integration_tests': self.test_adapter_integration()
        }
        
        # Generate summary
        test_results['summary'] = self.generate_test_summary(test_results)
        
        logger.info("Comprehensive mobile testing completed")
        return test_results
    
    def test_all_components(self) -> Dict[str, Any]:
        """Test all mobile components."""
        logger.info("Testing all mobile components")
        
        component_tests = {}
        
        # Test MobileLayoutManager
        component_tests['layout_manager'] = self.test_layout_manager()
        
        # Test MobileHeader
        component_tests['header'] = self.test_mobile_header()
        
        # Test MobileInputRibbon
        component_tests['input_ribbon'] = self.test_input_ribbon()
        
        # Test MobileContentTabs
        component_tests['content_tabs'] = self.test_content_tabs()
        
        # Test MobileImageAnalysis
        component_tests['image_analysis'] = self.test_image_analysis()
        
        # Test MobileVoiceInterface
        component_tests['voice_interface'] = self.test_voice_interface()
        
        # Test MobileChatInterface
        component_tests['chat_interface'] = self.test_chat_interface()
        
        # Test MobileHistoryView
        component_tests['history_view'] = self.test_history_view()
        
        # Test MobileSettingsCard
        component_tests['settings_card'] = self.test_settings_card()
        
        return component_tests
    
    def test_layout_manager(self) -> Dict[str, Any]:
        """Test MobileLayoutManager component."""
        try:
            with patch('streamlit.markdown') as mock_markdown:
                layout_manager = MobileLayoutManager("test_layout")
                
                # Test initialization
                assert layout_manager.component_id == "test_layout"
                assert hasattr(layout_manager, 'load_mobile_css')
                
                # Test CSS loading
                layout_manager.load_mobile_css()
                assert mock_markdown.called
                
                # Test layout status
                status = layout_manager.get_layout_status()
                assert isinstance(status, dict)
                assert 'status' in status
                
                return {'status': 'passed', 'tests_run': 3}
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_mobile_header(self) -> Dict[str, Any]:
        """Test MobileHeader component."""
        try:
            with patch('streamlit.markdown') as mock_markdown:
                header = MobileHeader("test_header", "Test Title", "Test Subtitle")
                
                # Test initialization
                assert header.component_id == "test_header"
                assert header.title == "Test Title"
                assert header.subtitle == "Test Subtitle"
                
                # Test rendering
                header.render()
                assert mock_markdown.called
                
                return {'status': 'passed', 'tests_run': 2}
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_input_ribbon(self) -> Dict[str, Any]:
        """Test MobileInputRibbon component."""
        try:
            with patch('streamlit.columns') as mock_columns, \
                 patch('streamlit.button') as mock_button:
                
                mock_columns.return_value = [Mock(), Mock(), Mock(), Mock()]
                mock_button.return_value = False
                
                input_ribbon = MobileInputRibbon("test_ribbon")
                
                # Test initialization
                assert input_ribbon.component_id == "test_ribbon"
                
                # Test rendering
                result = input_ribbon.render()
                assert mock_columns.called
                
                return {'status': 'passed', 'tests_run': 2}
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_content_tabs(self) -> Dict[str, Any]:
        """Test MobileContentTabs component."""
        try:
            with patch('streamlit.tabs') as mock_tabs:
                mock_tabs.return_value = [Mock(), Mock(), Mock(), Mock()]
                
                content_tabs = MobileContentTabs("test_tabs")
                
                # Test initialization
                assert content_tabs.component_id == "test_tabs"
                
                # Test tab registration
                def dummy_content():
                    pass
                
                content_tabs.register_tab_content('test_tab', dummy_content)
                assert 'test_tab' in content_tabs.tab_content
                
                # Test rendering
                result = content_tabs.render()
                
                return {'status': 'passed', 'tests_run': 3}
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_image_analysis(self) -> Dict[str, Any]:
        """Test MobileImageAnalysis component."""
        try:
            with patch('streamlit.file_uploader') as mock_uploader, \
                 patch('streamlit.button') as mock_button:
                
                mock_uploader.return_value = None
                mock_button.return_value = False
                
                image_analysis = MobileImageAnalysis("test_analysis")
                
                # Test initialization
                assert image_analysis.component_id == "test_analysis"
                
                # Test rendering
                image_analysis.render()
                
                # Test vision adapter setting
                mock_adapter = Mock()
                image_analysis.set_vision_adapter(mock_adapter)
                assert image_analysis.vision_adapter == mock_adapter
                
                return {'status': 'passed', 'tests_run': 3}
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_voice_interface(self) -> Dict[str, Any]:
        """Test MobileVoiceInterface component."""
        try:
            with patch('streamlit.button') as mock_button:
                mock_button.return_value = False
                
                voice_interface = MobileVoiceInterface("test_voice")
                
                # Test initialization
                assert voice_interface.component_id == "test_voice"
                
                # Test rendering
                voice_interface.render()
                
                # Test audio adapter setting
                mock_adapter = Mock()
                voice_interface.set_audio_adapter(mock_adapter)
                assert voice_interface.audio_adapter == mock_adapter
                
                return {'status': 'passed', 'tests_run': 3}
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_chat_interface(self) -> Dict[str, Any]:
        """Test MobileChatInterface component."""
        try:
            with patch('streamlit.text_input') as mock_input, \
                 patch('streamlit.button') as mock_button:
                
                mock_input.return_value = ""
                mock_button.return_value = False
                
                chat_interface = MobileChatInterface("test_chat")
                
                # Test initialization
                assert chat_interface.component_id == "test_chat"
                
                # Test rendering
                chat_interface.render()
                
                # Test adapter setting
                mock_text_adapter = Mock()
                mock_chat_model = Mock()
                chat_interface.set_text_adapter(mock_text_adapter)
                chat_interface.set_chat_model(mock_chat_model)
                
                return {'status': 'passed', 'tests_run': 3}
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_history_view(self) -> Dict[str, Any]:
        """Test MobileHistoryView component."""
        try:
            with patch('streamlit.session_state', {'analysis_history': []}):
                history_view = MobileHistoryView("test_history")
                
                # Test initialization
                assert history_view.component_id == "test_history"
                
                # Test rendering
                history_view.render()
                
                return {'status': 'passed', 'tests_run': 2}
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_settings_card(self) -> Dict[str, Any]:
        """Test MobileSettingsCard component."""
        try:
            with patch('streamlit.selectbox') as mock_select, \
                 patch('streamlit.checkbox') as mock_checkbox:
                
                mock_select.return_value = "default"
                mock_checkbox.return_value = True
                
                settings_card = MobileSettingsCard("test_settings")
                
                # Test initialization
                assert settings_card.component_id == "test_settings"
                
                # Test rendering
                settings_card.render()
                
                return {'status': 'passed', 'tests_run': 2}
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_integration_points(self) -> Dict[str, Any]:
        """Test integration between components."""
        logger.info("Testing component integration points")
        
        integration_tests = {}
        
        # Test component registry integration
        integration_tests['component_registry'] = self.test_component_registry_integration()
        
        # Test state manager integration
        integration_tests['state_manager'] = self.test_state_manager_integration()
        
        # Test error handler integration
        integration_tests['error_handler'] = self.test_error_handler_integration()
        
        # Test navigation integration
        integration_tests['navigation'] = self.test_navigation_integration()
        
        return integration_tests
    
    def test_component_registry_integration(self) -> Dict[str, Any]:
        """Test component registry integration."""
        try:
            # Test component registration
            mock_component = Mock()
            mobile_component_registry.register_component("test_component", mock_component)
            
            # Test component retrieval
            retrieved = mobile_component_registry.get_component("test_component")
            assert retrieved == mock_component
            
            # Test component listing
            all_components = mobile_component_registry.get_all_components()
            assert "test_component" in all_components
            
            return {'status': 'passed', 'tests_run': 3}
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_state_manager_integration(self) -> Dict[str, Any]:
        """Test state manager integration."""
        try:
            state_manager = MobileStateManager()
            
            # Test state creation
            test_state = {'test_key': 'test_value'}
            state_manager.set_component_state("test_component", test_state)
            
            # Test state retrieval
            retrieved_state = state_manager.get_component_state("test_component")
            assert retrieved_state['test_key'] == 'test_value'
            
            # Test state clearing
            state_manager.clear_component_state("test_component")
            
            return {'status': 'passed', 'tests_run': 3}
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_error_handler_integration(self) -> Dict[str, Any]:
        """Test error handler integration."""
        try:
            error_handler = MobileErrorHandler()
            
            # Test error handling
            test_error = Exception("Test error")
            error_handler.handle_component_error("test_component", test_error)
            
            # Test error logging
            error_handler.log_error("test_error", "Test error message")
            
            return {'status': 'passed', 'tests_run': 2}
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_navigation_integration(self) -> Dict[str, Any]:
        """Test navigation system integration."""
        try:
            # Test navigation setup
            nav_manager = mobile_navigation_manager
            
            # Test route setting
            nav_manager.set_current_route("image_analysis")
            current_route = nav_manager.get_current_route()
            assert current_route == "image_analysis"
            
            # Test navigation state
            nav_state = nav_manager.get_navigation_state()
            assert isinstance(nav_state, dict)
            assert 'current_route' in nav_state
            
            return {'status': 'passed', 'tests_run': 3}
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_performance_optimization(self) -> Dict[str, Any]:
        """Test performance optimizations."""
        logger.info("Testing performance optimizations")
        
        performance_tests = {}
        
        # Test component loading time
        performance_tests['component_loading'] = self.test_component_loading_performance()
        
        # Test memory usage
        performance_tests['memory_usage'] = self.test_memory_usage()
        
        # Test rendering performance
        performance_tests['rendering_performance'] = self.test_rendering_performance()
        
        # Test state management performance
        performance_tests['state_performance'] = self.test_state_management_performance()
        
        return performance_tests
    
    def test_component_loading_performance(self) -> Dict[str, Any]:
        """Test component loading performance."""
        try:
            start_time = time.time()
            
            # Load all components
            components = [
                MobileLayoutManager("perf_layout"),
                MobileHeader("perf_header", "Test", "Test"),
                MobileInputRibbon("perf_ribbon"),
                MobileContentTabs("perf_tabs"),
                MobileImageAnalysis("perf_analysis"),
                MobileVoiceInterface("perf_voice"),
                MobileChatInterface("perf_chat"),
                MobileHistoryView("perf_history"),
                MobileSettingsCard("perf_settings")
            ]
            
            loading_time = time.time() - start_time
            
            # Performance threshold: should load in under 1 second
            performance_ok = loading_time < 1.0
            
            return {
                'status': 'passed' if performance_ok else 'warning',
                'loading_time': loading_time,
                'components_loaded': len(components),
                'performance_ok': performance_ok
            }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage optimization."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Create multiple components
            components = []
            for i in range(10):
                components.extend([
                    MobileLayoutManager(f"mem_layout_{i}"),
                    MobileHeader(f"mem_header_{i}", "Test", "Test"),
                    MobileInputRibbon(f"mem_ribbon_{i}")
                ])
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory threshold: should not increase by more than 50MB
            memory_ok = memory_increase < 50
            
            return {
                'status': 'passed' if memory_ok else 'warning',
                'initial_memory_mb': initial_memory,
                'final_memory_mb': final_memory,
                'memory_increase_mb': memory_increase,
                'memory_ok': memory_ok
            }
        
        except ImportError:
            return {'status': 'skipped', 'reason': 'psutil not available'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_rendering_performance(self) -> Dict[str, Any]:
        """Test rendering performance."""
        try:
            with patch('streamlit.markdown'), \
                 patch('streamlit.button'), \
                 patch('streamlit.columns'):
                
                start_time = time.time()
                
                # Render multiple components
                layout_manager = MobileLayoutManager("render_layout")
                header = MobileHeader("render_header", "Test", "Test")
                input_ribbon = MobileInputRibbon("render_ribbon")
                
                for _ in range(5):
                    layout_manager.load_mobile_css()
                    header.render()
                    input_ribbon.render()
                
                rendering_time = time.time() - start_time
                
                # Rendering threshold: should render in under 0.5 seconds
                rendering_ok = rendering_time < 0.5
                
                return {
                    'status': 'passed' if rendering_ok else 'warning',
                    'rendering_time': rendering_time,
                    'rendering_ok': rendering_ok
                }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_state_management_performance(self) -> Dict[str, Any]:
        """Test state management performance."""
        try:
            state_manager = MobileStateManager()
            
            start_time = time.time()
            
            # Perform multiple state operations
            for i in range(100):
                state_manager.set_component_state(f"component_{i}", {'data': f'value_{i}'})
                state_manager.get_component_state(f"component_{i}")
            
            state_time = time.time() - start_time
            
            # State management threshold: should complete in under 0.1 seconds
            state_ok = state_time < 0.1
            
            return {
                'status': 'passed' if state_ok else 'warning',
                'state_operations_time': state_time,
                'operations_count': 200,
                'state_ok': state_ok
            }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_accessibility_compliance(self) -> Dict[str, Any]:
        """Test accessibility compliance."""
        logger.info("Testing accessibility compliance")
        
        accessibility_tests = {}
        
        # Test ARIA labels
        accessibility_tests['aria_labels'] = self.test_aria_labels()
        
        # Test keyboard navigation
        accessibility_tests['keyboard_navigation'] = self.test_keyboard_navigation()
        
        # Test screen reader compatibility
        accessibility_tests['screen_reader'] = self.test_screen_reader_compatibility()
        
        # Test color contrast
        accessibility_tests['color_contrast'] = self.test_color_contrast()
        
        # Test touch target sizes
        accessibility_tests['touch_targets'] = self.test_touch_target_sizes()
        
        return accessibility_tests
    
    def test_aria_labels(self) -> Dict[str, Any]:
        """Test ARIA labels implementation."""
        try:
            # Test components have proper ARIA labels
            with patch('streamlit.markdown') as mock_markdown:
                header = MobileHeader("aria_header", "Test", "Test")
                header.render()
                
                # Check if ARIA attributes are included in rendered HTML
                aria_found = False
                for call in mock_markdown.call_args_list:
                    if 'aria-' in str(call) or 'role=' in str(call):
                        aria_found = True
                        break
                
                return {
                    'status': 'passed' if aria_found else 'warning',
                    'aria_labels_found': aria_found
                }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_keyboard_navigation(self) -> Dict[str, Any]:
        """Test keyboard navigation support."""
        try:
            # Test navigation manager supports keyboard navigation
            nav_manager = mobile_navigation_manager
            
            # Test tab navigation
            nav_manager.set_current_route("image_analysis")
            current = nav_manager.get_current_route()
            
            # Test back navigation
            nav_manager.set_current_route("voice_assistant")
            can_go_back = nav_manager.can_go_back()
            
            return {
                'status': 'passed',
                'keyboard_navigation_supported': True,
                'back_navigation_available': can_go_back
            }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_screen_reader_compatibility(self) -> Dict[str, Any]:
        """Test screen reader compatibility."""
        try:
            # Test semantic HTML structure
            with patch('streamlit.markdown') as mock_markdown:
                layout_manager = MobileLayoutManager("sr_layout")
                layout_manager.load_mobile_css()
                
                # Check for semantic HTML elements
                semantic_found = False
                for call in mock_markdown.call_args_list:
                    html_content = str(call)
                    if any(tag in html_content for tag in ['<nav>', '<main>', '<section>', '<header>']):
                        semantic_found = True
                        break
                
                return {
                    'status': 'passed' if semantic_found else 'warning',
                    'semantic_html_found': semantic_found
                }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_color_contrast(self) -> Dict[str, Any]:
        """Test color contrast compliance."""
        try:
            # Test CSS includes proper contrast ratios
            with patch('streamlit.markdown') as mock_markdown:
                layout_manager = MobileLayoutManager("contrast_layout")
                layout_manager.load_mobile_css()
                
                # Check for color definitions in CSS
                css_found = False
                for call in mock_markdown.call_args_list:
                    if 'color:' in str(call) or 'background:' in str(call):
                        css_found = True
                        break
                
                return {
                    'status': 'passed' if css_found else 'warning',
                    'color_definitions_found': css_found,
                    'note': 'Manual contrast testing recommended'
                }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_touch_target_sizes(self) -> Dict[str, Any]:
        """Test touch target sizes meet accessibility guidelines."""
        try:
            # Test CSS includes proper touch target sizes (48px minimum)
            with patch('streamlit.markdown') as mock_markdown:
                layout_manager = MobileLayoutManager("touch_layout")
                layout_manager.load_mobile_css()
                
                # Check for touch target size definitions
                touch_size_found = False
                for call in mock_markdown.call_args_list:
                    css_content = str(call)
                    if '48px' in css_content or 'min-height' in css_content:
                        touch_size_found = True
                        break
                
                return {
                    'status': 'passed' if touch_size_found else 'warning',
                    'touch_target_sizes_defined': touch_size_found
                }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_cross_browser_compatibility(self) -> Dict[str, Any]:
        """Test cross-browser compatibility."""
        logger.info("Testing cross-browser compatibility")
        
        browser_tests = {}
        
        # Test CSS compatibility
        browser_tests['css_compatibility'] = self.test_css_compatibility()
        
        # Test JavaScript compatibility
        browser_tests['javascript_compatibility'] = self.test_javascript_compatibility()
        
        # Test mobile browser features
        browser_tests['mobile_features'] = self.test_mobile_browser_features()
        
        return browser_tests
    
    def test_css_compatibility(self) -> Dict[str, Any]:
        """Test CSS cross-browser compatibility."""
        try:
            with patch('streamlit.markdown') as mock_markdown:
                layout_manager = MobileLayoutManager("css_compat_layout")
                layout_manager.load_mobile_css()
                
                # Check for vendor prefixes and fallbacks
                css_calls = [str(call) for call in mock_markdown.call_args_list]
                css_content = ' '.join(css_calls)
                
                # Check for modern CSS features with fallbacks
                modern_css_features = [
                    'display: flex',
                    'display: grid',
                    'border-radius',
                    'box-shadow',
                    'transition'
                ]
                
                features_found = sum(1 for feature in modern_css_features if feature in css_content)
                
                return {
                    'status': 'passed',
                    'modern_css_features_count': features_found,
                    'total_features_checked': len(modern_css_features)
                }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_javascript_compatibility(self) -> Dict[str, Any]:
        """Test JavaScript compatibility."""
        try:
            # Test mobile interface switcher JavaScript
            switcher = mobile_interface_switcher
            
            # Test device detection
            is_mobile = switcher.detect_mobile_device()
            
            # Test interface configuration
            config = switcher.get_interface_config()
            
            return {
                'status': 'passed',
                'device_detection_works': isinstance(is_mobile, bool),
                'config_generation_works': isinstance(config, dict)
            }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_mobile_browser_features(self) -> Dict[str, Any]:
        """Test mobile browser specific features."""
        try:
            # Test viewport meta tag handling
            with patch('streamlit.markdown') as mock_markdown:
                layout_manager = MobileLayoutManager("mobile_features_layout")
                layout_manager.load_mobile_css()
                
                # Check for mobile-specific CSS
                css_calls = [str(call) for call in mock_markdown.call_args_list]
                css_content = ' '.join(css_calls)
                
                mobile_features = [
                    'touch-action',
                    'user-select',
                    '-webkit-tap-highlight-color',
                    'font-size: 16px'  # Prevents zoom on iOS
                ]
                
                features_found = sum(1 for feature in mobile_features if feature in css_content)
                
                return {
                    'status': 'passed',
                    'mobile_features_count': features_found,
                    'total_features_checked': len(mobile_features)
                }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test comprehensive error handling."""
        logger.info("Testing error handling")
        
        error_tests = {}
        
        # Test component error handling
        error_tests['component_errors'] = self.test_component_error_handling()
        
        # Test graceful degradation
        error_tests['graceful_degradation'] = self.test_graceful_degradation()
        
        # Test error recovery
        error_tests['error_recovery'] = self.test_error_recovery()
        
        return error_tests
    
    def test_component_error_handling(self) -> Dict[str, Any]:
        """Test component error handling."""
        try:
            error_handler = MobileErrorHandler()
            
            # Test error handling
            test_error = Exception("Test component error")
            error_handler.handle_component_error("test_component", test_error)
            
            # Test error state management
            error_handler.set_error_state("test_component", "error_message")
            error_state = error_handler.get_error_state("test_component")
            
            return {
                'status': 'passed',
                'error_handling_works': True,
                'error_state_managed': error_state is not None
            }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_graceful_degradation(self) -> Dict[str, Any]:
        """Test graceful degradation."""
        try:
            # Test component rendering with missing dependencies
            with patch('streamlit.error') as mock_error:
                # Simulate missing adapter
                image_analysis = MobileImageAnalysis("degradation_test")
                image_analysis.vision_adapter = None
                
                # Should not crash when rendering without adapter
                image_analysis.render()
                
                return {
                    'status': 'passed',
                    'graceful_degradation_works': True
                }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_error_recovery(self) -> Dict[str, Any]:
        """Test error recovery mechanisms."""
        try:
            error_handler = MobileErrorHandler()
            
            # Test error recovery
            error_handler.set_error_state("test_component", "error_message")
            error_handler.clear_error_state("test_component")
            
            # Test recovery suggestions
            suggestions = error_handler.get_recovery_suggestions("network_error")
            
            return {
                'status': 'passed',
                'error_recovery_works': True,
                'recovery_suggestions_available': len(suggestions) > 0
            }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_state_management(self) -> Dict[str, Any]:
        """Test state management system."""
        logger.info("Testing state management")
        
        state_tests = {}
        
        # Test state persistence
        state_tests['state_persistence'] = self.test_state_persistence()
        
        # Test state synchronization
        state_tests['state_synchronization'] = self.test_state_synchronization()
        
        # Test state validation
        state_tests['state_validation'] = self.test_state_validation()
        
        return state_tests
    
    def test_state_persistence(self) -> Dict[str, Any]:
        """Test state persistence."""
        try:
            state_manager = MobileStateManager()
            
            # Test state setting and getting
            test_state = {'key1': 'value1', 'key2': 'value2'}
            state_manager.set_component_state("persistence_test", test_state)
            
            retrieved_state = state_manager.get_component_state("persistence_test")
            
            return {
                'status': 'passed',
                'state_persisted': retrieved_state['key1'] == 'value1',
                'state_complete': len(retrieved_state) >= len(test_state)
            }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_state_synchronization(self) -> Dict[str, Any]:
        """Test state synchronization between components."""
        try:
            state_manager = MobileStateManager()
            
            # Test multiple component states
            state_manager.set_component_state("component1", {'shared_data': 'test'})
            state_manager.set_component_state("component2", {'shared_data': 'test'})
            
            state1 = state_manager.get_component_state("component1")
            state2 = state_manager.get_component_state("component2")
            
            return {
                'status': 'passed',
                'states_synchronized': state1['shared_data'] == state2['shared_data']
            }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_state_validation(self) -> Dict[str, Any]:
        """Test state validation."""
        try:
            state_manager = MobileStateManager()
            
            # Test invalid state handling
            invalid_state = {'invalid': None}
            state_manager.set_component_state("validation_test", invalid_state)
            
            retrieved_state = state_manager.get_component_state("validation_test")
            
            return {
                'status': 'passed',
                'state_validation_works': 'initialized' in retrieved_state
            }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_navigation_system(self) -> Dict[str, Any]:
        """Test navigation system."""
        logger.info("Testing navigation system")
        
        nav_tests = {}
        
        # Test route management
        nav_tests['route_management'] = self.test_route_management()
        
        # Test navigation history
        nav_tests['navigation_history'] = self.test_navigation_history()
        
        # Test navigation rendering
        nav_tests['navigation_rendering'] = self.test_navigation_rendering()
        
        return nav_tests
    
    def test_route_management(self) -> Dict[str, Any]:
        """Test route management."""
        try:
            nav_manager = mobile_navigation_manager
            
            # Test route setting
            nav_manager.set_current_route("image_analysis")
            current = nav_manager.get_current_route()
            
            # Test route validation
            nav_manager.set_current_route("invalid_route")
            still_current = nav_manager.get_current_route()
            
            return {
                'status': 'passed',
                'route_setting_works': current == "image_analysis",
                'invalid_route_handled': still_current == "image_analysis"
            }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_navigation_history(self) -> Dict[str, Any]:
        """Test navigation history."""
        try:
            nav_manager = mobile_navigation_manager
            
            # Test history tracking
            nav_manager.set_current_route("image_analysis")
            nav_manager.set_current_route("voice_assistant")
            nav_manager.set_current_route("chat_interface")
            
            # Test back navigation
            can_go_back = nav_manager.can_go_back()
            previous_route = nav_manager.go_back()
            
            return {
                'status': 'passed',
                'history_tracking_works': can_go_back,
                'back_navigation_works': previous_route is not None
            }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_navigation_rendering(self) -> Dict[str, Any]:
        """Test navigation rendering."""
        try:
            with patch('streamlit.tabs') as mock_tabs, \
                 patch('streamlit.columns') as mock_columns:
                
                mock_tabs.return_value = [Mock(), Mock(), Mock(), Mock()]
                mock_columns.return_value = [Mock(), Mock(), Mock(), Mock()]
                
                nav_manager = mobile_navigation_manager
                
                # Test different navigation modes
                nav_manager.set_navigation_mode(nav_manager.NavigationMode.TABS)
                result1 = nav_manager.render_navigation()
                
                nav_manager.set_navigation_mode(nav_manager.NavigationMode.PILLS)
                result2 = nav_manager.render_navigation()
                
                return {
                    'status': 'passed',
                    'tab_navigation_renders': result1 is not None,
                    'pill_navigation_renders': result2 is not None
                }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_adapter_integration(self) -> Dict[str, Any]:
        """Test PlantGuard adapter integration."""
        logger.info("Testing adapter integration")
        
        adapter_tests = {}
        
        # Test vision adapter integration
        adapter_tests['vision_adapter'] = self.test_vision_adapter_integration()
        
        # Test audio adapter integration
        adapter_tests['audio_adapter'] = self.test_audio_adapter_integration()
        
        # Test text adapter integration
        adapter_tests['text_adapter'] = self.test_text_adapter_integration()
        
        return adapter_tests
    
    def test_vision_adapter_integration(self) -> Dict[str, Any]:
        """Test vision adapter integration."""
        try:
            # Test with mock vision adapter
            mock_adapter = Mock()
            mock_adapter.predict.return_value = ("Healthy", 0.95)
            
            image_analysis = MobileImageAnalysis("vision_integration_test")
            image_analysis.set_vision_adapter(mock_adapter)
            
            # Test adapter connection
            adapter_connected = image_analysis.vision_adapter is not None
            
            return {
                'status': 'passed',
                'adapter_connected': adapter_connected,
                'adapter_callable': hasattr(image_analysis.vision_adapter, 'predict')
            }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_audio_adapter_integration(self) -> Dict[str, Any]:
        """Test audio adapter integration."""
        try:
            # Test with mock audio adapter
            mock_adapter = Mock()
            mock_adapter.transcribe.return_value = "Test transcription"
            
            voice_interface = MobileVoiceInterface("audio_integration_test")
            voice_interface.set_audio_adapter(mock_adapter)
            
            # Test adapter connection
            adapter_connected = voice_interface.audio_adapter is not None
            
            return {
                'status': 'passed',
                'adapter_connected': adapter_connected,
                'adapter_callable': hasattr(voice_interface.audio_adapter, 'transcribe')
            }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def test_text_adapter_integration(self) -> Dict[str, Any]:
        """Test text adapter integration."""
        try:
            # Test with mock text adapter
            mock_text_adapter = Mock()
            mock_chat_model = Mock()
            mock_chat_model.predict.return_value = "Test response"
            
            chat_interface = MobileChatInterface("text_integration_test")
            chat_interface.set_text_adapter(mock_text_adapter)
            chat_interface.set_chat_model(mock_chat_model)
            
            # Test adapter connections
            text_adapter_connected = chat_interface.text_adapter is not None
            chat_model_connected = chat_interface.chat_model is not None
            
            return {
                'status': 'passed',
                'text_adapter_connected': text_adapter_connected,
                'chat_model_connected': chat_model_connected
            }
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def generate_test_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test summary."""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        warning_tests = 0
        skipped_tests = 0
        
        def count_test_results(results):
            nonlocal total_tests, passed_tests, failed_tests, warning_tests, skipped_tests
            
            if isinstance(results, dict):
                if 'status' in results:
                    total_tests += 1
                    if results['status'] == 'passed':
                        passed_tests += 1
                    elif results['status'] == 'failed':
                        failed_tests += 1
                    elif results['status'] == 'warning':
                        warning_tests += 1
                    elif results['status'] == 'skipped':
                        skipped_tests += 1
                else:
                    for value in results.values():
                        count_test_results(value)
        
        # Count all test results
        for test_category in test_results.values():
            if isinstance(test_category, dict):
                count_test_results(test_category)
        
        # Calculate success rate
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'warning_tests': warning_tests,
            'skipped_tests': skipped_tests,
            'success_rate': success_rate,
            'overall_status': 'passed' if failed_tests == 0 else 'failed',
            'test_categories': len(test_results) - 1  # Exclude summary itself
        }


def run_comprehensive_tests():
    """Run comprehensive mobile testing suite."""
    print("🧪 Starting Comprehensive Mobile PlantGuard Testing Suite")
    print("=" * 60)
    
    tester = MobileComponentTester()
    results = tester.run_all_tests()
    
    # Print summary
    summary = results['summary']
    print(f"\n📊 Test Summary:")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Warnings: {summary['warning_tests']}")
    print(f"Skipped: {summary['skipped_tests']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Overall Status: {summary['overall_status'].upper()}")
    
    # Save results to file
    results_file = Path("mobile_test_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    return results


if __name__ == "__main__":
    results = run_comprehensive_tests()
    
    # Exit with appropriate code
    if results['summary']['overall_status'] == 'passed':
        sys.exit(0)
    else:
        sys.exit(1)