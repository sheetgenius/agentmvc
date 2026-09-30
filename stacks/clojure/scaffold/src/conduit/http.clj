(ns conduit.http
  (:require [muuntaja.core :as muuntaja]
            [reitit.coercion.malli :as malli]
            [reitit.ring :as ring]
            [reitit.ring.coercion :as coercion]
            [reitit.ring.middleware.muuntaja :as format]
            [reitit.ring.middleware.parameters :as parameters]))

(defn handler [_data-source]
  (ring/ring-handler
   (ring/router
    [["/health" {:get (fn [_] {:status 200 :body {:status "ok"}})}]]
    {:data {:muuntaja muuntaja/instance
            :coercion malli/coercion
            :middleware [parameters/parameters-middleware
                         format/format-negotiate-middleware
                         format/format-response-middleware
                         format/format-request-middleware
                         coercion/coerce-request-middleware
                         coercion/coerce-response-middleware]}})
   (ring/create-default-handler)))
