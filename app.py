from flask import Flask, render_template, request,jsonify
from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import logging
import pymongo
logging.basicConfig(filename="scrapper.log" , level=logging.INFO)

app = Flask(__name__)

@app.route("/", methods = ['GET'])
def homepage():
    return render_template("index.html")

@app.route("/review" , methods = ['POST' , 'GET'])
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ","") #replace a;l the space like iphone    7 is considered as iphone 7 only
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            uClient = uReq(flipkart_url)
            flipkartPage = uClient.read()
            uClient.close()
            flipkart_html = bs(flipkartPage, "html.parser")
            bigboxes = flipkart_html.find_all("div", {"class": "cPHDOP col-12-12"})
            del bigboxes[0:3]
            box = bigboxes[0]
            productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
            prodRes = requests.get(productLink, headers={"User-Agent": "Mozilla/5.0"})
            if prodRes.status_code != 200:
               print(f"Failed to fetch product page: {prodRes.status_code}")
               return "Failed to fetch product details"
            prodRes.encoding='utf-8'
            prod_html = bs(prodRes.text, "html.parser")
            print(prod_html)
            commentboxes = prod_html.find_all('div', {'class': "RcXBOT"})

            filename = searchString + ".csv"
            fw = open(filename, "w")
            headers = "Product, Customer Name, Rating, Heading, Comment \n"
            fw.write(headers)
            reviews = []
            for commentbox in commentboxes:
                try:
                    #name.encode(encoding='utf-8')
                    name = commentbox.find('p', {'class': '_2NsDsF AwS1CA'})
                    name = name.text if name else "No Name"

                except:
                    logging.info("name")

                try:
                    #rating.encode(encoding='utf-8')
                    rating = commentbox.find("div", {"class": "XQDdHH Ga3i8K"})  # Updated class for ratings
                    rating = rating.text if rating else "No Rating"

                except:
                    rating = 'No Rating'
                    logging.info("rating")

                try:
                    #commentHead.encode(encoding='utf-8')
                    commentHead = commentbox.find("div", {"class": "z9E0IG"}).text

                except:
                    commentHead = 'No Comment Heading'
                    logging.info(commentHead)
                try:
                    custComment = commentbox.find("div", {"class": "ZmyHeo"}).text
                except Exception as e:
                    logging.info(e)

                mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,
                          "Comment": custComment}
                reviews.append(mydict)
            logging.info("log my final result {}".format(reviews))
            
            client= pymongo.MongoClient("mongodb+srv://nishatkhanam10prl:nishat30@cluster0.w7vmw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
            db=client['review_scrap']
            review_col= db['review_scrap_data']
            review_col.insert_many(reviews)
            
            return render_template('result.html', reviews=reviews[0:(len(reviews)-1)])
        except Exception as e:
            logging.info(e)
            return 'something is wrong'
    # return render_template('results.html')

    else:
        return render_template('index.html')


if __name__=="__main__":
    app.run(host="0.0.0.0")