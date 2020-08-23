<?php
require 'db.php5';
try {
    $pdo = Database::connect();
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_OBJ);
    $stmt = $pdo->query("select * from login");
    $result = $stmt->fetch(PDO::FETCH_ASSOC);
    print_r($result);
    Database::disconnect();
} catch (PDOException $e) {
    //nothing
}
?>
