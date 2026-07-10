# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests

cnx = st.connection("snowflake")
session = cnx.session()

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

name_on_order = st.text_input('Name on Smoothie:')
st.write("The name on your Smoothie will be:", name_on_order)

# .collect() returns Snowpark Row objects and avoids the native Arrow -> pandas
# conversion (to_pandas) that segfaults on this environment.
rows = (
    session.table("smoothies.public.fruit_options")
    .select(col('FRUIT_NAME'), col('SEARCH_ON'))
    .collect()
)

# Build plain-Python structures from the rows -- no pandas, no pyarrow
fruit_names = [row['FRUIT_NAME'] for row in rows]
search_map = {row['FRUIT_NAME']: row['SEARCH_ON'] for row in rows}

ingredients_list = st.multiselect('Choose up to 5 ingredients:', fruit_names, max_selections=5)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        search_on = str(search_map[fruit_chosen]).strip()

        st.subheader(fruit_chosen + ' Nutrition Information')

        smoothiefroot_response = requests.get(
            "https://my.smoothiefroot.com/api/fruit/" + search_on
        )

        if smoothiefroot_response.status_code == 200:
            # st.json renders without going through pyarrow (unlike st.dataframe / st.table)
            st.json(smoothiefroot_response.json())
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
