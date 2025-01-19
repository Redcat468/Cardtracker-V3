const { createApp } = Vue;

createApp({
    data() {
        return {
            searchTerm: '',
            operations: [], // Les opérations seront chargées depuis le backend
            statusGeo: [], // Liste des statuts géographiques
            cards: [], // Liste des cartes correspondant au statut source
            offloadStatuses: [], // Liste des statuts offload
            selectedSource: '', // Statut source sélectionné
            selectedTarget: '', // Statut cible sélectionné
            selectedCard: '', // Carte sélectionnée
            currentOffloadStatus: '', // Statut offload actuel de la carte sélectionnée
            selectedOffloadStatus: '', // Nouveau statut offload sélectionné
            showDeleteConfirmation: false,
            operationToDelete: null,
        };
    },
    methods: {
        // Filtre les opérations en fonction du champ de recherche
        filterOperations() {
            return this.operations.filter(operation =>
                operation.card_name.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
                operation.username.toLowerCase().includes(this.searchTerm.toLowerCase())
            );
        },
        // Charge les cartes disponibles pour le statut source sélectionné
        updateCards() {
            if (this.selectedSource) {
                fetch(`/get_cards_by_status/${this.selectedSource}`)
                    .then(response => response.json())
                    .then(data => {
                        this.cards = data;
                        this.selectedCard = ''; // Réinitialiser la sélection
                        this.currentOffloadStatus = ''; // Réinitialiser le statut offload
                    })
                    .catch(error => console.error('Erreur lors de la récupération des cartes :', error));
            } else {
                this.cards = [];
                this.selectedCard = '';
                this.currentOffloadStatus = '';
            }
        }
        
        // Soumet le formulaire pour déplacer une carte
        moveCard() {
            if (this.selectedCard && this.selectedTarget) {
                fetch('/track', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        card: this.selectedCard,
                        source: this.selectedSource,
                        target: this.selectedTarget,
                        offload_status: this.selectedOffloadStatus,
                    }),
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert(`Carte ${this.selectedCard} déplacée avec succès.`);
                            this.updateCards(); // Met à jour les cartes disponibles
                        } else {
                            alert(data.message || 'Erreur lors du déplacement de la carte.');
                        }
                    })
                    .catch(error => console.error('Erreur lors du déplacement de la carte :', error));
            } else {
                alert('Veuillez sélectionner une carte, une source et une destination.');
            }
        },
        // Affiche la boîte de confirmation pour la suppression
        confirmDelete(operation) {
            this.operationToDelete = operation;
            this.showDeleteConfirmation = true;
        },
        // Annule la suppression
        cancelDelete() {
            this.showDeleteConfirmation = false;
            this.operationToDelete = null;
        },
        // Supprime une opération après confirmation
        deleteOperation() {
            if (this.operationToDelete) {
                fetch(`/cancel_operation/${this.operationToDelete.id}`, {
                    method: 'POST',
                })
                    .then(response => {
                        if (response.ok) {
                            this.operations = this.operations.filter(op => op.id !== this.operationToDelete.id);
                            this.showDeleteConfirmation = false;
                            this.operationToDelete = null;
                        } else {
                            alert('Erreur lors de la suppression de l'opération.');
                        }
                    })
                    .catch(error => console.error('Erreur lors de la suppression de l'opération :', error));
            }
        },
    },
    mounted() {
        // Chargement initial des statuts géographiques
        fetch('/get_status_geo')
            .then(response => response.json())
            .then(data => {
                this.statusGeo = data;
                if (this.statusGeo.length > 0) {
                    this.selectedSource = this.statusGeo[0].status_name;
                    this.updateCards();
                }
            })
            .catch(error => console.error('Erreur lors du chargement des statuts géographiques :', error));

        // Chargement des statuts offload
        fetch('/get_offload_status_list')
            .then(response => response.json())
            .then(data => {
                this.offloadStatuses = data;
            })
            .catch(error => console.error('Erreur lors du chargement des statuts offload :', error));

        // Chargement initial des opérations
        fetch('/get_operations')
            .then(response => response.json())
            .then(data => {
                this.operations = data;
            })
            .catch(error => console.error('Erreur lors du chargement des opérations :', error));
    },
}).mount('#app');
