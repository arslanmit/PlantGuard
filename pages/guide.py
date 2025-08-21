"""Guide Page for PlantGuard Redesigned UI.

Usage guide, photo tips, privacy information, and FAQ.
"""

import logging

import streamlit as st

logger = logging.getLogger(__name__)


def render_guide_page():
    """Render the guide page."""
    st.markdown(
        """
        <div class='page-header'>
            <h2 class='page-title'>User Guide</h2>
            <p class='page-subtitle'>
                Learn how to use PlantGuard effectively for plant health analysis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Guide sections
    tab1, tab2, tab3, tab4 = st.tabs(["📷 Photo Tips", "🔒 Privacy", "❓ FAQ", "🚀 Getting Started"])

    with tab1:
        render_photo_tips()

    with tab2:
        render_privacy_info()

    with tab3:
        render_faq()

    with tab4:
        render_getting_started()


def render_photo_tips():
    """Render photo tips section."""
    st.markdown("### 📷 Taking Great Plant Photos")

    st.markdown("""
    Getting accurate disease detection results starts with taking good photos. Here are our top tips:
    """)

    # Photo quality tips
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        #### ✅ **Do This:**

        **🌞 Lighting**
        - Use natural daylight when possible
        - Avoid harsh shadows
        - Take photos during mid-morning or late afternoon

        **📐 Composition**
        - Fill the frame with the leaf
        - Keep the leaf flat and in focus
        - Include the entire affected area

        **📱 Camera Settings**
        - Use the highest resolution available
        - Enable auto-focus
        - Hold the camera steady
        """)

    with col2:
        st.markdown("""
        #### ❌ **Avoid This:**

        **💡 Poor Lighting**
        - Direct flash photography
        - Very dark or dim conditions
        - Strong backlighting

        **📸 Poor Composition**
        - Blurry or out-of-focus images
        - Too much background clutter
        - Extreme close-ups that miss context

        **🚫 Technical Issues**
        - Low resolution images
        - Heavy image compression
        - Tilted or rotated photos
        """)

    # Example images section
    st.markdown("---")
    st.markdown("### 🖼️ Example Photos")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **✅ Good Example**
        - Clear, well-lit leaf
        - Visible disease symptoms
        - Minimal background
        """)
        st.info("📷 Example image would be shown here")

    with col2:
        st.markdown("""
        **⚠️ Okay Example**
        - Decent lighting
        - Some background clutter
        - Symptoms partially visible
        """)
        st.warning("📷 Example image would be shown here")

    with col3:
        st.markdown("""
        **❌ Poor Example**
        - Dark or blurry
        - Too much background
        - Symptoms not clear
        """)
        st.error("📷 Example image would be shown here")

    # Disease-specific tips
    st.markdown("---")
    st.markdown("### 🦠 Disease-Specific Photo Tips")

    with st.expander("🍃 Leaf Spots and Blight", expanded=False):
        st.markdown("""
        - Capture both the spots and surrounding healthy tissue
        - Show the pattern and distribution of spots
        - Include multiple affected leaves if possible
        - Photograph both upper and lower leaf surfaces
        """)

    with st.expander("🍄 Fungal Diseases", expanded=False):
        st.markdown("""
        - Look for fuzzy growth, discoloration, or unusual textures
        - Capture the progression from healthy to affected areas
        - Show any spores or fungal structures if visible
        - Document environmental conditions (humidity, air circulation)
        """)

    with st.expander("🐛 Pest Damage", expanded=False):
        st.markdown("""
        - Show the damage pattern (holes, chewing marks, etc.)
        - Include any visible pests if present
        - Capture the scale of the damage
        - Document the location on the plant
        """)


def render_privacy_info():
    """Render privacy information section."""
    st.markdown("### 🔒 Privacy & Data Protection")

    st.success("""
    **🛡️ Your Privacy is Our Priority**

    PlantGuard is designed with privacy-first principles. All plant analysis happens locally on your device.
    """)

    # Privacy principles
    st.markdown("#### 🔐 Core Privacy Principles")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **🏠 Local Processing**
        - All AI models run on your device
        - No images sent to external servers
        - No internet required for analysis

        **🗑️ No Data Storage**
        - Images processed in memory only
        - Temporary files deleted immediately
        - No persistent data collection
        """)

    with col2:
        st.markdown("""
        **🔒 Zero Tracking**
        - No user accounts required
        - No personal data collected
        - No usage analytics sent externally

        **🌐 Offline Capable**
        - Works without internet connection
        - No external API dependencies
        - Complete data sovereignty
        """)

    # GDPR compliance
    st.markdown("---")
    st.markdown("#### 🇪🇺 GDPR Compliance")

    st.info("""
    **PlantGuard is fully GDPR compliant:**

    - **Right to Privacy**: No personal data is collected or processed
    - **Data Minimization**: Only necessary image data is processed temporarily
    - **Purpose Limitation**: Data used only for plant disease detection
    - **Storage Limitation**: No data stored beyond the current session
    - **Transparency**: This privacy notice explains all data handling
    """)

    # Technical details
    with st.expander("🔧 Technical Privacy Details", expanded=False):
        st.markdown("""
        **Data Flow:**
        1. You upload/capture an image
        2. Image processed locally by AI models
        3. Results displayed to you
        4. Image data deleted from memory
        5. No data leaves your device

        **Temporary Files:**
        - Created only during processing
        - Stored in secure temporary directories
        - Automatically deleted after analysis
        - Never transmitted externally

        **Session Data:**
        - Chat history stored in browser memory only
        - Analysis results kept for current session
        - All data cleared when you close the app
        """)

    # Contact information
    st.markdown("---")
    st.markdown("#### 📧 Privacy Questions?")

    st.markdown("""
    If you have questions about our privacy practices:

    - 📧 Email: privacy@plantguard.ai
    - 📖 Full Privacy Policy: [Link to detailed policy]
    - 🛡️ Data Protection Officer: dpo@plantguard.ai
    """)


def render_faq():
    """Render FAQ section."""
    st.markdown("### ❓ Frequently Asked Questions")

    # General questions
    st.markdown("#### 🌱 General Questions")

    with st.expander("What types of plants can PlantGuard analyze?", expanded=False):
        st.markdown("""
        PlantGuard can analyze a wide variety of plants, including:

        - **Vegetables**: Tomatoes, peppers, cucumbers, lettuce, etc.
        - **Fruits**: Apples, citrus, berries, grapes, etc.
        - **Ornamental plants**: Roses, houseplants, garden flowers
        - **Trees**: Fruit trees, shade trees, ornamental trees
        - **Herbs**: Basil, mint, rosemary, and other culinary herbs

        The system works best with common agricultural and garden plants.
        """)

    with st.expander("How accurate is the disease detection?", expanded=False):
        st.markdown("""
        PlantGuard achieves over 90% accuracy on our validation dataset, but real-world accuracy depends on:

        - **Photo quality**: Clear, well-lit images work best
        - **Disease stage**: Early symptoms may be harder to detect
        - **Plant variety**: Common plants have better accuracy
        - **Image conditions**: Proper lighting and focus are crucial

        Always consult with agricultural experts for critical decisions.
        """)

    with st.expander("Can I use PlantGuard offline?", expanded=False):
        st.markdown("""
        **Yes! PlantGuard is designed to work completely offline.**

        - All AI models run locally on your device
        - No internet connection required for analysis
        - Perfect for use in remote locations
        - Your data never leaves your device

        You only need internet for the initial app download.
        """)

    # Technical questions
    st.markdown("#### 🔧 Technical Questions")

    with st.expander("What image formats are supported?", expanded=False):
        st.markdown("""
        **Supported formats:**
        - ✅ JPEG (.jpg, .jpeg)
        - ✅ PNG (.png)

        **File requirements:**
        - Maximum size: 200MB per image
        - Minimum resolution: 224x224 pixels
        - Color images work best

        **Not supported:**
        - GIF, BMP, TIFF formats
        - RAW camera files
        - Video files
        """)

    with st.expander("Why is my analysis taking a long time?", expanded=False):
        st.markdown("""
        Analysis time depends on several factors:

        **Normal processing time:** 5-15 seconds

        **Factors that may slow processing:**
        - Large image files (>50MB)
        - Older or slower devices
        - Multiple images being processed
        - First-time model loading

        **To speed up analysis:**
        - Resize images before uploading
        - Close other applications
        - Use one image at a time
        """)

    with st.expander("Can I analyze multiple images at once?", expanded=False):
        st.markdown("""
        **Yes! PlantGuard supports batch analysis.**

        - Upload multiple images simultaneously
        - Each image is analyzed individually
        - Results are shown for each image
        - Progress tracking for batch operations

        **Batch processing tips:**
        - Limit to 10 images per batch for best performance
        - Ensure all images meet quality requirements
        - Allow extra time for processing multiple images
        """)

    # Usage questions
    st.markdown("#### 🎯 Usage Questions")

    with st.expander("What should I do if the diagnosis seems wrong?", expanded=False):
        st.markdown("""
        If you think the diagnosis is incorrect:

        **Immediate steps:**
        1. Try taking a clearer photo with better lighting
        2. Capture multiple angles of the affected area
        3. Include more context (surrounding healthy tissue)
        4. Check if symptoms match the suggested disease

        **Always remember:**
        - PlantGuard is a diagnostic aid, not a replacement for expert advice
        - Consult with local agricultural extension services
        - Consider multiple factors (weather, care history, etc.)
        - When in doubt, seek professional plant pathologist advice
        """)

    with st.expander("How do I get the best results?", expanded=False):
        st.markdown("""
        **For optimal results:**

        **Photo quality:**
        - Use natural daylight
        - Keep the camera steady
        - Fill the frame with the affected leaf
        - Ensure the image is in focus

        **Timing:**
        - Photograph symptoms as soon as you notice them
        - Take photos during the day for best lighting
        - Document progression over time

        **Context:**
        - Include both affected and healthy tissue
        - Note environmental conditions
        - Consider recent weather or care changes
        """)


def render_getting_started():
    """Render getting started guide."""
    st.markdown("### 🚀 Getting Started with PlantGuard")

    st.markdown("""
    Welcome to PlantGuard! This quick guide will help you get the most out of our plant disease detection system.
    """)

    # Step-by-step guide
    st.markdown("#### 📋 Quick Start Guide")

    step1, step2, step3 = st.columns(3)

    with step1:
        st.markdown("""
        **1️⃣ Choose Input Method**

        On the Home page, select your preferred input:
        - 📷 **Camera**: Take a live photo
        - 🖼️ **Upload**: Select from your device
        - 🎙️ **Voice**: Ask questions (coming soon)
        - ⌨️ **Text**: Type your questions
        """)

    with step2:
        st.markdown("""
        **2️⃣ Capture/Upload Image**

        For best results:
        - Use good lighting
        - Focus on affected areas
        - Include healthy tissue for context
        - Ensure image is clear and sharp
        """)

    with step3:
        st.markdown("""
        **3️⃣ Review Results**

        PlantGuard will show you:
        - Disease identification
        - Confidence level
        - Treatment recommendations
        - Additional information
        """)

    # Feature overview
    st.markdown("---")
    st.markdown("#### 🎯 Key Features")

    feature1, feature2 = st.columns(2)

    with feature1:
        st.markdown("""
        **🔍 Analysis Features:**
        - Real-time disease detection
        - Confidence scoring
        - Treatment recommendations
        - Multiple input methods
        - Batch image processing
        """)

    with feature2:
        st.markdown("""
        **📊 Management Features:**
        - Analysis history tracking
        - Image comparison tools
        - Export capabilities
        - Privacy-first design
        - Offline functionality
        """)

    # Tips for success
    st.markdown("---")
    st.markdown("#### 💡 Tips for Success")

    st.info("""
    **🎯 Best Practices:**

    1. **Start Simple**: Begin with clear, obvious symptoms
    2. **Multiple Angles**: Take photos from different perspectives
    3. **Document Progress**: Track changes over time using the Compare feature
    4. **Use History**: Review past analyses in the History section
    5. **Ask Questions**: Use the text chat for specific concerns
    6. **Stay Updated**: Check the Guide regularly for new tips
    """)

    # Troubleshooting
    with st.expander("🔧 Common Issues & Solutions", expanded=False):
        st.markdown("""
        **Problem: Blurry or unclear results**
        - Solution: Retake photo with better lighting and focus

        **Problem: "No disease detected" when symptoms are visible**
        - Solution: Try closer photos of affected areas

        **Problem: Slow processing**
        - Solution: Reduce image size or close other applications

        **Problem: App not responding**
        - Solution: Refresh the page and try again

        **Problem: Unexpected results**
        - Solution: Verify photo quality and try multiple images
        """)

    # Next steps
    st.markdown("---")
    st.markdown("#### 🎯 Ready to Start?")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🏠 Go to Home", type="primary"):
            st.session_state.current_page = "Home"
            st.rerun()

    with col2:
        if st.button("📷 Photo Tips"):
            st.session_state.current_page = "Guide"
            # Switch to photo tips tab (would need tab state management)
            st.rerun()

    with col3:
        if st.button("⚙️ Settings"):
            st.session_state.current_page = "Settings"
            st.rerun()
