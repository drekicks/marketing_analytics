# import streamlit as st
# import pandas as pd
# import numpy as np
#
# st.title("My First Streamlit App")
#
# # Add a interactive slider
# num_points = st.slider("Select number of points", 10, 100, 50)
#
# # Generate data and display a chart instantly
# chart_data = pd.DataFrame(np.random.randn(num_points, 2), columns=['x', 'y'])
# st.line_chart(chart_data)

import pandas as pd
import streamlit as st

st.title("My First Streamlit App")

# Add a text input and slider widget
user_name = st.text_input("Enter your name:", "Data Enthusiast")
sample_count = st.slider("Select number of data points", 10, 100, 50)

st.write(f"Hello, {user_name}! Here is your chart:")

# Generate interactive chart
chart_data = pd.DataFrame({"Data": range(sample_count)})
st.line_chart(chart_data)