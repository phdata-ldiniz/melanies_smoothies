# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas as pd

cnx = st.connection("snowflake")
session = cnx.session()

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

name_on_order = st.text_input('Name on Smoothie:')
st.write("The name on your Smoothie will be:", name_on_order)

my_dataframe = (
    session.table("smoothies.public.fruit_options")
    .select(col('FRUIT_NAME'), col('SEARCH_ON'))
)

# Convert to pandas so we can use .loc for the SEARCH_ON lookup
pd_df = my_dataframe.to_pandas()

# Build the dropdown from a plain list of strings -> fruit_chosen is always a clean str
fruit_names = pd_df['FRUIT_NAME'].tolist()
ingredients_list = st.multiselect('Choose up to 5 ingredients:', fruit_names, max_selections=5)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        # Look up the API search term for this fruit
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        search_on = str(search_on).strip()

        st.subheader(fruit_chosen + ' Nutrition Information')

        smoothiefroot_response = requests.get(
            "https://my.smoothiefroot.com/api/fruit/" + search_on
        )

        if smoothiefroot_response.status_code == 200:
            # Normalize the JSON into a real DataFrame BEFORE handing it to st.dataframe.
            # Passing raw nested JSON straight to st.dataframe is what trips the Arrow layer.
            sf_df = pd.json_normalize(smoothiefroot_response.json())
            st.dataframe(data=sf_df, use_container_width=True)
        else:
            st.warning(
                f"No nutrition info found for '{search_on}' "
                f"(status {smoothiefroot_response.status_code})."
            )

    my_insert_stmt = (
        "insert into smoothies.public.orders(ingredients, name_on_order) "
        "values ('" + ingredients_string + "', '" + name_on_order + "')"
    )

    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success('Your Smoothie is ordered, ' + name_on_order + '!', icon="✅")
