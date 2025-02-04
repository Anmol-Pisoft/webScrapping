import streamlit as st
import requests
from bs4 import BeautifulSoup
import logging
import pymongo
import csv
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="scraper.log",
    filemode="w",  # Overwrite the file each time (use "a" to append)
)

# Streamlit App
st.set_page_config(page_title="Flipkart Review Scraper", page_icon="🛒")
st.title("Flipkart Review Scraper")

# Input for product searchdsfsdf
search_string = st.text_input("Enter the product to search for:", placeholder="e.g., iPhone 15")
if st.button("Scrape Reviews"):
    if search_string:
        try:
            search_string = search_string.replace(" ", "")
            flipkart_url = f"https://www.flipkart.com/search?q={search_string}"

            # Fetch Flipkart search page
            logging.info("Fetching Flipkart search page...") 
            uClient = requests.get(flipkart_url)
            uClient.raise_for_status()  # Raise an error for bad status codes
            flipkart_page = uClient.content
            flipkart_html = BeautifulSoup(flipkart_page, "html.parser")

            # Extract product link
            logging.info("Extracting product link...")
            bigboxes = flipkart_html.findAll("div", {"class": "cPHDOP col-12-12"})
            if not bigboxes:
                st.error("No products found. Please check the search query.")
                logging.error("No products found in the search results.")
            else:
                # Find the first product link
                product_link = None
                for box in bigboxes:
                    try:
                        product_link = "https://www.flipkart.com" + box.div.div.div.a['href']
                        break
                    except:
                        continue

                if not product_link:
                    st.error("No product link found. Please check the search query.")
                    logging.error("No product link found in the search results.")
                else:
                    # Fetch product page
                    logging.info("Fetching product page...")
                    prod_res = requests.get(product_link)
                    prod_res.encoding = 'utf-8'
                    prod_html = BeautifulSoup(prod_res.text, "html.parser")

                    # Extract reviews
                    logging.info("Extracting reviews...")
                    comment_boxes = prod_html.find_all('div', {'class': "RcXBOT"})
                    if not comment_boxes:
                        st.error("No reviews found for this product.")
                        logging.error("No reviews found on the product page.")
                    else:
                        reviews = []
                        for commentbox in comment_boxes:
                            try:
                                name = commentbox.div.div.find_all('p', {'class': '_2NsDsF AwS1CA'})[0].text
                            except:
                                name = "No Name"
                                logging.info("Name not found")

                            try:
                                rating = commentbox.div.div.div.div.text
                            except:
                                rating = "No Rating"
                                logging.info("Rating not found")

                            try:
                                comment_head = commentbox.div.div.div.p.text
                            except:
                                comment_head = "No Comment Heading"
                                logging.info("Comment heading not found")

                            try:
                                comtag = commentbox.div.div.find_all('div', {'class': ''})
                                cust_comment = comtag[0].div.text
                            except Exception as e:
                                cust_comment = "No Comment"
                                logging.info(f"Comment not found: {e}")

                            # Store review in a dictionary
                            mydict = {
                                "Product": search_string,
                                "Name": name,
                                "Rating": rating,
                                "CommentHead": comment_head,
                                "Comment": cust_comment
                            }
                            reviews.append(mydict)

                        # Display reviews in a table
                        st.write("### Scraped Reviews")
                        st.table(reviews)

                        # Save reviews to CSV
                        filename = f"{search_string}.csv"
                        with open(filename, "w", newline="", encoding="utf-8") as fw:
                            writer = csv.DictWriter(fw, fieldnames=["Product", "Name", "Rating", "CommentHead", "Comment"])
                            writer.writeheader()
                            writer.writerows(reviews)
                        st.success(f"Reviews saved to {filename}")

                        # Save reviews to MongoDB
                        uri = "mongodb+srv://anmolrana909:iaTVvWpQauCIZTja@webscrapcluster.ss56b.mongodb.net/?retryWrites=true&w=majority&appName=WebScrapCluster"
                        try:
                            client = pymongo.MongoClient(uri)
                            db = client['WebScrapCluster']
                            coll_pw = db['PROJECT 0']
                            coll_pw.insert_many(reviews)

                            # Confirm MongoDB connection
                            client.admin.command('ping')
                            st.success("Successfully connected to MongoDB!")
                        except pymongo.errors.OperationFailure as e:
                            logging.error(f"MongoDB authentication failed: {e}")
                            st.error("Failed to connect to MongoDB. Please check your credentials.")
                        except Exception as e:
                            logging.error(f"MongoDB connection error: {e}")
                            st.error(f"Failed to connect to MongoDB: {e}")

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            st.error("Failed to fetch data from Flipkart. Please check your network connection.")
        except Exception as e:
            logging.error(f"Error occurred: {e}", exc_info=True)
            st.error(f"Something went wrong during scraping. Error: {e}")
    else:
        st.warning("Please enter a product name to search.")