Inven3 - Inventory Management System

Inven3 is a simple yet powerful Inventory Management System built with Flask and SQLite. It allows users to manage products, locations (warehouses), and logistics (movement of goods). This application is designed for ease of use and flexibility, making it a suitable solution for managing inventory and tracking stock movements.

Features

- Product Management: Add, view, update, and delete products.
- Location Management: Manage warehouse locations and view their details.
- Logistics Management: Track and manage the movement of products between locations.
- Summary Dashboard: View a summary of products and locations.

Requirements

- Python 3.6+
- Flask
- SQLite

Installation

1. Clone the Repository

   ```bash
   git clone https://github.com/namir008/inven3.git
   cd inven3
   ```

2. Set Up a Virtual Environment

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install Dependencies

   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the Database

   The application automatically creates the necessary database tables when it runs for the first time. You can run it to initialize the database.

   ```bash
   python app.py
   ```

Usage

1. Run the Application

   ```bash
   python app.py
   ```

   The application will start on `http://127.0.0.1:5000/`.

2. Access the Application

   Open your web browser and go to `http://127.0.0.1:5000/` to access the summary page. Use the navigation links to manage products, locations, and logistics.

Application Routes

- `/`: A dashboard showing an overview of products and locations.
- `/product`: Add and manage products.
- `/location`: Add and manage warehouse locations.
- `/movement`: Track and manage product movements between locations.
- `/delete`: Delete products or locations.
- `/edit`: Edit product or location details.

Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Make your changes.
4. Commit your changes (`git commit -am 'Add some feature'`).
5. Push to the branch (`git push origin feature/your-feature`).
6. Create a new Pull Request.

Contact

For any questions or suggestions, feel free to reach out:

- Email: nabilmustaphaofficial@gmail.com
